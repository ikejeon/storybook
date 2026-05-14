// swift-tools-version: 5.9
import PackageDescription

let package = Package(
    name: "MoonJarStoriesiOS",
    platforms: [
        .iOS(.v17),
        .macOS(.v14)
    ],
    products: [
        .executable(name: "MoonJarStoriesiOS", targets: ["MoonJarStoriesiOS"])
    ],
    targets: [
        .executableTarget(
            name: "MoonJarStoriesiOS",
            path: "Sources/MoonJarStoriesiOS",
            resources: [
                .copy("Resources/AppIcon.png"),
                .copy("Resources/shared-content")
            ]
        ),
        .testTarget(
            name: "MoonJarStoriesiOSTests",
            dependencies: ["MoonJarStoriesiOS"],
            path: "Tests/MoonJarStoriesiOSTests"
        )
    ]
)
