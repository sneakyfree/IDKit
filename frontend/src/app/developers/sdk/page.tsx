"use client";

import { useState } from "react";
import {
    Code2,
    Download,
    Copy,
    CheckCircle,
    Terminal,
    BookOpen,
    Package,
} from "lucide-react";

/**
 * SDK Download & Documentation Page
 *
 * Multi-language SDK download with install instructions and quickstart.
 * Closes Helix Scan gap X09-2.
 */

type Language = "typescript" | "python" | "go" | "ruby";

interface SDKInfo {
    name: string;
    package: string;
    version: string;
    installCmd: string;
    quickstart: string;
    docsUrl: string;
    icon: string;
}

const SDK_DATA: Record<Language, SDKInfo> = {
    typescript: {
        name: "TypeScript / JavaScript",
        package: "@idkit/sdk",
        version: "2.0.0",
        installCmd: "npm install @idkit/sdk",
        quickstart: `import { IDKitClient } from '@idkit/sdk';

const client = new IDKitClient({
  apiKey: 'your-api-key',
  baseUrl: 'https://api.idkit.io/v1',
});

// Create AI-generated content
const content = await client.content.generate({
  prompt: 'Write a tweet about AI tools',
  platform: 'twitter',
  tone: 'professional',
});

console.log(content.text);
// Schedule it
await client.schedule.create({
  contentId: content.id,
  publishAt: '2026-03-01T10:00:00Z',
  platforms: ['twitter', 'linkedin'],
});`,
        docsUrl: "/developers/docs/typescript",
        icon: "TS",
    },
    python: {
        name: "Python",
        package: "idkit",
        version: "2.0.0",
        installCmd: "pip install idkit",
        quickstart: `from idkit import IDKitClient

client = IDKitClient(
    api_key="your-api-key",
    base_url="https://api.idkit.io/v1",
)

# Create AI-generated content
content = client.content.generate(
    prompt="Write a tweet about AI tools",
    platform="twitter",
    tone="professional",
)

print(content.text)

# Fetch analytics
analytics = client.analytics.summary(
    period="last_30_days",
    platforms=["twitter", "linkedin"],
)
print(f"Total reach: {analytics.total_reach}")`,
        docsUrl: "/developers/docs/python",
        icon: "PY",
    },
    go: {
        name: "Go",
        package: "github.com/idkit/idkit-go",
        version: "2.0.0",
        installCmd: "go get github.com/idkit/idkit-go@latest",
        quickstart: `package main

import (
    "context"
    "fmt"
    idkit "github.com/idkit/idkit-go"
)

func main() {
    client := idkit.NewClient(
        idkit.WithAPIKey("your-api-key"),
    )

    // Create content
    content, err := client.Content.Generate(context.Background(), &idkit.GenerateRequest{
        Prompt:   "Write a tweet about AI tools",
        Platform: "twitter",
    })
    if err != nil {
        panic(err)
    }
    fmt.Println(content.Text)
}`,
        docsUrl: "/developers/docs/go",
        icon: "GO",
    },
    ruby: {
        name: "Ruby",
        package: "idkit",
        version: "2.0.0",
        installCmd: "gem install idkit",
        quickstart: `require 'idkit'

client = Idkit::Client.new(
  api_key: 'your-api-key',
  base_url: 'https://api.idkit.io/v1'
)

# Create content
content = client.content.generate(
  prompt: 'Write a tweet about AI tools',
  platform: 'twitter',
  tone: 'professional'
)

puts content.text

# List scheduled posts
posts = client.schedule.list(status: 'pending')
posts.each { |p| puts "#{p.title} → #{p.publish_at}" }`,
        docsUrl: "/developers/docs/ruby",
        icon: "RB",
    },
};

const LANGUAGES: Language[] = ["typescript", "python", "go", "ruby"];

export default function SDKPage() {
    const [selectedLang, setSelectedLang] = useState<Language>("typescript");
    const [copied, setCopied] = useState<string | null>(null);

    const sdk = SDK_DATA[selectedLang];

    const copyToClipboard = (text: string, label: string) => {
        navigator.clipboard.writeText(text);
        setCopied(label);
        setTimeout(() => setCopied(null), 2000);
    };

    return (
        <div className="min-h-screen bg-gray-950 text-white p-6">
            <div className="max-w-5xl mx-auto">
                {/* Header */}
                <div className="text-center mb-12">
                    <div className="flex items-center justify-center gap-3 mb-4">
                        <Package className="w-10 h-10 text-purple-400" />
                        <h1 className="text-3xl font-bold">IDKit SDKs</h1>
                    </div>
                    <p className="text-gray-200 max-w-xl mx-auto">
                        Official client libraries for the IDKit API. Auto-generated from OpenAPI spec,
                        fully typed, and ready for production.
                    </p>
                </div>

                {/* Language Tabs */}
                <div className="flex gap-2 justify-center mb-8">
                    {LANGUAGES.map((lang) => (
                        <button
                            key={lang}
                            onClick={() => setSelectedLang(lang)}
                            className={`flex items-center gap-2 px-5 py-3 rounded-xl font-medium transition-all ${selectedLang === lang
                                    ? "bg-purple-600 text-white shadow-lg shadow-purple-600/25"
                                    : "bg-gray-900 text-gray-200 hover:text-white hover:bg-gray-800 border border-gray-800"
                                }`}
                        >
                            <span className="text-xs font-mono font-bold opacity-75">{SDK_DATA[lang].icon}</span>
                            {SDK_DATA[lang].name}
                        </button>
                    ))}
                </div>

                {/* SDK Info Card */}
                <div className="bg-gray-900 border border-gray-800 rounded-2xl overflow-hidden">
                    {/* Install Section */}
                    <div className="p-6 border-b border-gray-800">
                        <div className="flex items-center gap-2 text-gray-200 text-sm mb-3">
                            <Terminal className="w-4 h-4" />
                            <span>Installation</span>
                        </div>
                        <div className="flex items-center justify-between bg-gray-950 rounded-lg px-4 py-3 font-mono text-sm">
                            <code className="text-green-400">$ {sdk.installCmd}</code>
                            <button
                                onClick={() => copyToClipboard(sdk.installCmd, "install")}
                                className="p-1.5 hover:bg-gray-800 rounded transition-colors"
                            >
                                {copied === "install" ? (
                                    <CheckCircle className="w-4 h-4 text-green-400" />
                                ) : (
                                    <Copy className="w-4 h-4 text-gray-300" />
                                )}
                            </button>
                        </div>
                        <div className="flex items-center gap-4 mt-3 text-sm text-gray-300">
                            <span>Package: <code className="text-gray-300">{sdk.package}</code></span>
                            <span>Version: <code className="text-gray-300">v{sdk.version}</code></span>
                        </div>
                    </div>

                    {/* Quickstart Section */}
                    <div className="p-6">
                        <div className="flex items-center justify-between mb-3">
                            <div className="flex items-center gap-2 text-gray-200 text-sm">
                                <Code2 className="w-4 h-4" />
                                <span>Quickstart</span>
                            </div>
                            <button
                                onClick={() => copyToClipboard(sdk.quickstart, "quickstart")}
                                className="flex items-center gap-1.5 px-3 py-1.5 bg-gray-800 rounded-lg hover:bg-gray-700 transition-colors text-sm"
                            >
                                {copied === "quickstart" ? (
                                    <><CheckCircle className="w-3.5 h-3.5 text-green-400" /> Copied</>
                                ) : (
                                    <><Copy className="w-3.5 h-3.5" /> Copy</>
                                )}
                            </button>
                        </div>
                        <pre className="bg-gray-950 rounded-lg p-4 overflow-x-auto text-sm leading-relaxed">
                            <code className="text-gray-300">{sdk.quickstart}</code>
                        </pre>
                    </div>
                </div>

                {/* Bottom Links */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-8">
                    <a
                        href="/developers"
                        className="flex items-center gap-3 p-4 bg-gray-900 border border-gray-800 rounded-xl hover:border-gray-700 transition-colors"
                    >
                        <BookOpen className="w-5 h-5 text-purple-400" />
                        <div>
                            <p className="font-medium">API Reference</p>
                            <p className="text-sm text-gray-300">Full endpoint documentation</p>
                        </div>
                    </a>
                    <a
                        href="/developers/webhooks"
                        className="flex items-center gap-3 p-4 bg-gray-900 border border-gray-800 rounded-xl hover:border-gray-700 transition-colors"
                    >
                        <Code2 className="w-5 h-5 text-blue-400" />
                        <div>
                            <p className="font-medium">Webhooks</p>
                            <p className="text-sm text-gray-300">Event-driven integrations</p>
                        </div>
                    </a>
                    <a
                        href="https://github.com/idkit"
                        target="_blank"
                        rel="noopener noreferrer"
                        className="flex items-center gap-3 p-4 bg-gray-900 border border-gray-800 rounded-xl hover:border-gray-700 transition-colors"
                    >
                        <Download className="w-5 h-5 text-green-400" />
                        <div>
                            <p className="font-medium">GitHub</p>
                            <p className="text-sm text-gray-300">Source code & examples</p>
                        </div>
                    </a>
                </div>
            </div>
        </div>
    );
}
