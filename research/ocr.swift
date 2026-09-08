// Local Apple Vision OCR for our generated synthetic benchmark images.
// No networking, language correction, or candidate dictionary.
import Foundation
import Vision

var results: [[String: Any]] = []
for path in CommandLine.arguments.dropFirst() {
    do {
        let request = VNRecognizeTextRequest()
        request.recognitionLevel = .accurate
        request.usesLanguageCorrection = false
        request.recognitionLanguages = ["en-US"]
        let handler = VNImageRequestHandler(url: URL(fileURLWithPath: path), options: [:])
        try handler.perform([request])
        let observations = (request.results ?? []).compactMap { item -> [String: Any]? in
            guard let candidate = item.topCandidates(1).first else { return nil }
            return ["text": candidate.string, "confidence": candidate.confidence]
        }
        results.append(["file": path, "observations": observations, "revision": request.revision])
    } catch {
        results.append(["file": path, "error": String(describing: error)])
    }
}
let data = try JSONSerialization.data(withJSONObject: results, options: [.prettyPrinted, .sortedKeys])
FileHandle.standardOutput.write(data)
