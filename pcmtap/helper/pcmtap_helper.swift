// pcmtap-helper: stream what processes are playing, as raw PCM, to stdout.
//
// Uses Core Audio process taps (macOS 14.2+): a tap on the chosen processes (or on
// every process), wrapped in a private aggregate device whose IOProc receives the
// tapped audio. Output is interleaved little-endian float32 on stdout; the first
// line on stderr is a JSON object describing it:
//   {"event":"format","sample_rate":48000,"channels":2,"sample_format":"f32le"}
//
// Usage:
//   pcmtap-helper --list                       JSON array of audio processes
//   pcmtap-helper [--pid N]... [--bundle-id PREFIX]... [--exclude] [--mute] [--seconds S]
// With no --pid/--bundle-id, taps every process. --exclude inverts the selection
// (tap everything except those). --mute silences the tapped processes on the
// speakers while they are recorded. Stops after --seconds, on SIGINT/SIGTERM, when
// stdin closes, or when stdout is closed.

import AudioToolbox
import CoreAudio
import Foundation

// MARK: - errors and output

func emit(_ object: [String: Any]) {
    if let data = try? JSONSerialization.data(withJSONObject: object),
        let line = String(data: data, encoding: .utf8)
    {
        FileHandle.standardError.write((line + "\n").data(using: .utf8)!)
    }
}

func fail(_ message: String, _ status: OSStatus = 0, code: Int32 = 1) -> Never {
    emit(["event": "error", "message": message, "status": Int(status)])
    exit(code)
}

func check(_ status: OSStatus, _ what: String) {
    if status != noErr { fail("\(what) failed (OSStatus \(status))", status) }
}

// MARK: - permission (TCC "System Audio Recording")

// Without this permission a tap delivers silence rather than an error, so the state is
// asked of TCC directly (the private calls Apple's AudioCap sample uses).
let tccService = "kTCCServiceAudioCapture" as CFString
typealias PreflightFn = @convention(c) (CFString, CFDictionary?) -> Int
typealias RequestFn = @convention(c) (CFString, CFDictionary?, @escaping (Bool) -> Void) -> Void
let tcc = dlopen("/System/Library/PrivateFrameworks/TCC.framework/Versions/A/TCC", RTLD_NOW)

func permissionStatus() -> String {
    guard let tcc, let sym = dlsym(tcc, "TCCAccessPreflight") else { return "unknown" }
    switch unsafeBitCast(sym, to: PreflightFn.self)(tccService, nil) {
    case 0: return "granted"
    case 1: return "denied"
    default: return "not_determined"
    }
}

func requestPermission() -> Bool {
    guard let tcc, let sym = dlsym(tcc, "TCCAccessRequest") else { return false }
    let done = DispatchSemaphore(value: 0)
    var granted = false
    unsafeBitCast(sym, to: RequestFn.self)(tccService, nil) { ok in
        granted = ok
        done.signal()
    }
    done.wait()
    return granted
}

// MARK: - responsibility

// macOS attributes a process's privacy permissions to its "responsible" process: the
// terminal app (or, under a detached tmux or a daemon, nothing that can show a prompt).
// Re-spawning ourselves with responsibility disclaimed makes this helper responsible
// for itself, so the permission is asked for, and remembered, as pcmtap-helper.
@_silgen_name("responsibility_spawnattrs_setdisclaim")
func responsibility_spawnattrs_setdisclaim(
    _ attrs: UnsafeMutablePointer<posix_spawnattr_t?>, _ disclaim: Int32) -> Int32

func respawnDisclaimed() -> Never {
    setenv("PCMTAP_DISCLAIMED", "1", 1)
    var attrs: posix_spawnattr_t?
    posix_spawnattr_init(&attrs)
    _ = responsibility_spawnattrs_setdisclaim(&attrs, 1)
    let path = Bundle.main.executablePath ?? CommandLine.arguments[0]
    var argv: [UnsafeMutablePointer<CChar>?] = CommandLine.arguments.map { strdup($0) } + [nil]
    var child: pid_t = 0
    let status = posix_spawn(&child, path, nil, &attrs, &argv, environ)
    if status != 0 { fail("could not re-spawn the helper (errno \(status))") }
    for sig in [SIGINT, SIGTERM] {
        signal(sig, SIG_IGN)
        let source = DispatchSource.makeSignalSource(signal: sig, queue: .global())
        source.setEventHandler { kill(child, sig) }
        source.resume()
        parentSources.append(source)
    }
    var result: Int32 = 0
    while waitpid(child, &result, 0) < 0 && errno == EINTR {}
    exit((result & 0x7f) == 0 ? (result >> 8) & 0xff : 128 + (result & 0x7f))
}
var parentSources: [DispatchSourceSignal] = []

if getenv("PCMTAP_DISCLAIMED") == nil && getenv("PCMTAP_NO_DISCLAIM") == nil {
    respawnDisclaimed()
}

// MARK: - property helpers

func address(_ selector: AudioObjectPropertySelector) -> AudioObjectPropertyAddress {
    AudioObjectPropertyAddress(
        mSelector: selector, mScope: kAudioObjectPropertyScopeGlobal,
        mElement: kAudioObjectPropertyElementMain)
}

func readValue<T>(_ object: AudioObjectID, _ selector: AudioObjectPropertySelector, _ initial: T)
    -> T?
{
    var addr = address(selector)
    var value = initial
    var size = UInt32(MemoryLayout<T>.size)
    let status = AudioObjectGetPropertyData(object, &addr, 0, nil, &size, &value)
    return status == noErr ? value : nil
}

func readArray(_ object: AudioObjectID, _ selector: AudioObjectPropertySelector) -> [AudioObjectID] {
    var addr = address(selector)
    var size: UInt32 = 0
    guard AudioObjectGetPropertyDataSize(object, &addr, 0, nil, &size) == noErr, size > 0 else {
        return []
    }
    var ids = [AudioObjectID](repeating: 0, count: Int(size) / MemoryLayout<AudioObjectID>.size)
    guard AudioObjectGetPropertyData(object, &addr, 0, nil, &size, &ids) == noErr else { return [] }
    return ids
}

func readString(_ object: AudioObjectID, _ selector: AudioObjectPropertySelector) -> String? {
    var addr = address(selector)
    var value: Unmanaged<CFString>?
    var size = UInt32(MemoryLayout<Unmanaged<CFString>?>.size)
    let status = withUnsafeMutablePointer(to: &value) {
        AudioObjectGetPropertyData(object, &addr, 0, nil, &size, $0)
    }
    guard status == noErr, let cf = value?.takeRetainedValue() else { return nil }
    return cf as String
}

// MARK: - processes

struct AudioProcess {
    let object: AudioObjectID
    let pid: pid_t
    let bundleID: String
    let isRunningOutput: Bool
}

func audioProcesses() -> [AudioProcess] {
    readArray(AudioObjectID(kAudioObjectSystemObject), kAudioHardwarePropertyProcessObjectList)
        .map { obj in
            AudioProcess(
                object: obj,
                pid: readValue(obj, kAudioProcessPropertyPID, pid_t(-1)) ?? -1,
                bundleID: readString(obj, kAudioProcessPropertyBundleID) ?? "",
                isRunningOutput: (readValue(obj, kAudioProcessPropertyIsRunningOutput, UInt32(0)) ?? 0)
                    != 0)
        }
}

// MARK: - arguments

var pids: [pid_t] = []
var bundlePrefixes: [String] = []
var exclude = false
var mute = false
var seconds: Double? = nil
var list = false

var args = CommandLine.arguments.dropFirst().makeIterator()
while let arg = args.next() {
    switch arg {
    case "--pid":
        guard let v = args.next(), let p = pid_t(v) else { fail("--pid needs a number", code: 2) }
        pids.append(p)
    case "--bundle-id":
        guard let v = args.next() else { fail("--bundle-id needs a value", code: 2) }
        bundlePrefixes.append(v)
    case "--exclude": exclude = true
    case "--mute": mute = true
    case "--seconds":
        guard let v = args.next(), let s = Double(v), s > 0 else {
            fail("--seconds needs a positive number", code: 2)
        }
        seconds = s
    case "--list": list = true
    case "--permission":
        print(permissionStatus())
        exit(0)
    case "--request-permission":
        let before = permissionStatus()
        let granted = before == "granted" || requestPermission()
        print(granted ? "granted" : permissionStatus())
        exit(granted ? 0 : 4)
    case "--version":
        print("pcmtap-helper 1")
        exit(0)
    default: fail("unknown argument \(arg)", code: 2)
    }
}

if list {
    let rows: [[String: Any]] = audioProcesses().map {
        ["pid": Int($0.pid), "bundle_id": $0.bundleID, "running_output": $0.isRunningOutput]
    }
    let data = try! JSONSerialization.data(withJSONObject: rows, options: [.prettyPrinted])
    FileHandle.standardOutput.write(data)
    FileHandle.standardOutput.write("\n".data(using: .utf8)!)
    exit(0)
}

// MARK: - the tap

if permissionStatus() == "denied" {
    fail(
        "System Audio Recording is denied for pcmtap-helper: allow it in System Settings > "
            + "Privacy & Security > Screen & System Audio Recording", code: 4)
}

let selecting = !pids.isEmpty || !bundlePrefixes.isEmpty
let chosen: [AudioObjectID] = audioProcesses()
    .filter { p in pids.contains(p.pid) || bundlePrefixes.contains { p.bundleID.hasPrefix($0) } }
    .map { $0.object }
if selecting && !exclude && chosen.isEmpty {
    fail(
        "no audio process matches \(pids.map(String.init) + bundlePrefixes); "
            + "the app must be running and have opened audio output (play something once)",
        code: 3)
}

let description: CATapDescription =
    (selecting && !exclude)
    ? CATapDescription(stereoMixdownOfProcesses: chosen)
    : CATapDescription(stereoGlobalTapButExcludeProcesses: chosen)
description.uuid = UUID()
description.name = "pcmtap"
description.isPrivate = true
description.muteBehavior = mute ? .mutedWhenTapped : .unmuted

var tapID = AudioObjectID(kAudioObjectUnknown)
check(AudioHardwareCreateProcessTap(description, &tapID), "AudioHardwareCreateProcessTap")

guard var format = readValue(tapID, kAudioTapPropertyFormat, AudioStreamBasicDescription()) else {
    fail("could not read the tap's audio format")
}
let isFloat32 =
    format.mFormatID == kAudioFormatLinearPCM && format.mFormatFlags & kAudioFormatFlagIsFloat != 0
    && format.mBitsPerChannel == 32
if !isFloat32 { fail("unexpected tap format (not float32 linear PCM)") }
let channels = Int(format.mChannelsPerFrame)
let interleaved = format.mFormatFlags & kAudioFormatFlagIsNonInterleaved == 0

guard
    let outputDevice = readValue(
        AudioObjectID(kAudioObjectSystemObject), kAudioHardwarePropertyDefaultSystemOutputDevice,
        AudioDeviceID(0)),
    let outputUID = readString(outputDevice, kAudioDevicePropertyDeviceUID)
else { fail("could not find the system output device") }

let aggregate: [String: Any] = [
    kAudioAggregateDeviceNameKey: "pcmtap",
    kAudioAggregateDeviceUIDKey: UUID().uuidString,
    kAudioAggregateDeviceMainSubDeviceKey: outputUID,
    kAudioAggregateDeviceIsPrivateKey: true,
    kAudioAggregateDeviceIsStackedKey: false,
    kAudioAggregateDeviceTapAutoStartKey: true,
    kAudioAggregateDeviceSubDeviceListKey: [[kAudioSubDeviceUIDKey: outputUID]],
    kAudioAggregateDeviceTapListKey: [
        [kAudioSubTapDriftCompensationKey: true, kAudioSubTapUIDKey: description.uuid.uuidString]
    ],
]
var aggregateID = AudioObjectID(kAudioObjectUnknown)
check(
    AudioHardwareCreateAggregateDevice(aggregate as CFDictionary, &aggregateID),
    "AudioHardwareCreateAggregateDevice")

// MARK: - streaming

signal(SIGPIPE, SIG_IGN)
let stdoutFD = FileHandle.standardOutput.fileDescriptor
let ioQueue = DispatchQueue(label: "pcmtap.io", qos: .userInteractive)
var stopped = false
var procID: AudioDeviceIOProcID?
var interleaveBuffer = [Float32]()

func cleanup() {
    if let procID {
        AudioDeviceStop(aggregateID, procID)
        AudioDeviceDestroyIOProcID(aggregateID, procID)
    }
    AudioHardwareDestroyAggregateDevice(aggregateID)
    AudioHardwareDestroyProcessTap(tapID)
}

func stop(_ reason: String, code: Int32 = 0) -> Never {
    cleanup()
    emit(["event": "stopped", "reason": reason])
    exit(code)
}

func writeAll(_ pointer: UnsafeRawPointer, _ count: Int) -> Bool {
    var offset = 0
    while offset < count {
        let n = write(stdoutFD, pointer + offset, count - offset)
        if n <= 0 { return false }
        offset += n
    }
    return true
}

check(
    AudioDeviceCreateIOProcIDWithBlock(&procID, aggregateID, ioQueue) { _, input, _, _, _ in
        if stopped { return }
        let buffers = UnsafeMutableAudioBufferListPointer(UnsafeMutablePointer(mutating: input))
        var ok = true
        if interleaved || buffers.count == 1 {
            for buffer in buffers {
                if let data = buffer.mData { ok = ok && writeAll(data, Int(buffer.mDataByteSize)) }
            }
        } else {  // one buffer per channel: interleave
            let frames = Int(buffers[0].mDataByteSize) / MemoryLayout<Float32>.size
            interleaveBuffer.removeAll(keepingCapacity: true)
            interleaveBuffer.reserveCapacity(frames * buffers.count)
            let planes = buffers.map { $0.mData!.assumingMemoryBound(to: Float32.self) }
            for f in 0..<frames { for plane in planes { interleaveBuffer.append(plane[f]) } }
            ok = interleaveBuffer.withUnsafeBytes { writeAll($0.baseAddress!, $0.count) }
        }
        if !ok {
            stopped = true
            DispatchQueue.main.async { stop("stdout closed") }
        }
    }, "AudioDeviceCreateIOProcIDWithBlock")

emit([
    "event": "format", "sample_rate": format.mSampleRate, "channels": interleaved ? channels : channels,
    "sample_format": "f32le", "tap_processes": chosen.count, "muted": mute,
])
check(AudioDeviceStart(aggregateID, procID), "AudioDeviceStart")

var sources: [DispatchSourceSignal] = []
for sig in [SIGINT, SIGTERM] {
    signal(sig, SIG_IGN)
    let source = DispatchSource.makeSignalSource(signal: sig, queue: .main)
    source.setEventHandler { stop("signal \(sig)") }
    source.resume()
    sources.append(source)
}
if let seconds {
    DispatchQueue.main.asyncAfter(deadline: .now() + seconds) { stop("duration reached") }
}
// stdin closing (the parent went away) also stops the capture
DispatchQueue.global().async {
    while FileHandle.standardInput.availableData.count > 0 {}
    DispatchQueue.main.async { stop("stdin closed") }
}
dispatchMain()
