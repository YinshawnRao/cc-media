import AppKit
import Foundation

func fail(_ message: String) -> Never {
    FileHandle.standardError.write(Data((message + "\n").utf8))
    exit(1)
}

let args = CommandLine.arguments
guard args.count == 4 else {
    fail("usage: watermark <output.png> <text> <font-size>")
}

let outputURL = URL(fileURLWithPath: args[1])
let text = args[2]
guard let fontSizeValue = Double(args[3]) else {
    fail("invalid font size: \(args[3])")
}

let fontSize = CGFloat(fontSizeValue)
let font = NSFont.systemFont(ofSize: fontSize, weight: .semibold)
let paragraph = NSMutableParagraphStyle()
paragraph.alignment = .left
paragraph.lineBreakMode = .byClipping

let attrs: [NSAttributedString.Key: Any] = [
    .font: font,
    .foregroundColor: NSColor.white.withAlphaComponent(0.90),
    .paragraphStyle: paragraph,
]

let nsText = text as NSString
let measured = nsText.size(withAttributes: attrs)
let padX = ceil(fontSize * 0.62)
let padY = ceil(fontSize * 0.36)
let width = ceil(measured.width + padX * 2)
let height = ceil(measured.height + padY * 2)

let image = NSImage(size: NSSize(width: width, height: height))
image.lockFocus()
NSColor.clear.setFill()
NSRect(x: 0, y: 0, width: width, height: height).fill()

let radius = max(4, fontSize * 0.34)
let box = NSBezierPath(
    roundedRect: NSRect(x: 0, y: 0, width: width, height: height),
    xRadius: radius,
    yRadius: radius
)
NSColor(calibratedWhite: 0.0, alpha: 0.38).setFill()
box.fill()

let textY = (height - measured.height) / 2
nsText.draw(at: NSPoint(x: padX, y: textY), withAttributes: attrs)
image.unlockFocus()

guard
    let tiff = image.tiffRepresentation,
    let bitmap = NSBitmapImageRep(data: tiff),
    let png = bitmap.representation(using: .png, properties: [:])
else {
    fail("failed to create PNG")
}

do {
    try png.write(to: outputURL)
} catch {
    fail("failed to write \(outputURL.path): \(error)")
}
