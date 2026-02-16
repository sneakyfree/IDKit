'use client';
import { useState } from 'react';
import Link from 'next/link';

const FAQ_DATA = [
  { name: "Getting Started", icon: "🚀", items: [
    { q: "What is IDKit?", a: "IDKit is an AI-powered platform for influencers to automate content creation, build digital twins, and scale their brand without being on camera 24/7." },
    { q: "Who is IDKit for?", a: "Content creators, influencers, podcasters, and personal brands who want to produce more content, faster, with AI assistance." },
    { q: "How do I get started?", a: "Sign up, upload voice samples for AI twin training, connect your social accounts, and start generating content in minutes." },
    { q: "Do I need technical skills?", a: "No. IDKit is designed for creators, not developers. TikTok-level simplicity - scroll, tap, create." },
  ]},
  { name: "AI Twins", icon: "🤖", items: [
    { q: "What is an AI Twin?", a: "A digital avatar that looks and sounds like you. It can appear in videos, answer comments, and create content while you focus on strategy." },
    { q: "How realistic are AI Twins?", a: "Very. We use state-of-the-art voice cloning and video synthesis. Most viewers can't tell the difference." },
    { q: "How much training data do I need?", a: "Minimum 10 minutes of clear audio for voice cloning. More data = better results. Video twins need 5+ minutes of face footage." },
    { q: "Can I control what my twin says?", a: "Absolutely. You approve all content before posting. Set guidelines, review scripts, and maintain full creative control." },
  ]},
  { name: "Content Creation", icon: "✨", items: [
    { q: "What content can IDKit generate?", a: "Scripts, captions, posts, stories, podcast episodes, video ideas, hashtags, and more. Multi-platform formatting included." },
    { q: "How does trend detection work?", a: "We monitor social platforms for viral trends in your niche. Get alerts and ready-to-use content hooks." },
    { q: "Can I schedule posts?", a: "Yes. Create content queues, set posting schedules, and let IDKit publish automatically across platforms." },
    { q: "Does it work with my existing brand voice?", a: "Yes. Train IDKit on your existing content to match your style, tone, and vocabulary." },
  ]},
  { name: "Podcast Lab", icon: "🎙️", items: [
    { q: "How does AI podcast creation work?", a: "Give us a topic, we generate a script, synthesize voices (yours or AI hosts), add music, and produce a ready-to-publish episode." },
    { q: "Can I have conversations between AI hosts?", a: "Yes. Create multi-voice podcasts with different AI personalities having natural conversations." },
    { q: "Where can I publish podcasts?", a: "Direct integration with Spotify, Apple Podcasts, Google Podcasts, YouTube, and RSS feeds." },
    { q: "What about music and sound effects?", a: "Built-in library of royalty-free music and sound effects. Or upload your own licensed assets." },
  ]},
  { name: "Privacy & Security", icon: "🔒", items: [
    { q: "Is my voice data safe?", a: "Yes. Voice samples are encrypted at rest and in transit. We never use your data to train models for others." },
    { q: "Can I delete my data?", a: "Anytime. Delete your AI twin, voice samples, and all generated content with one click." },
    { q: "Who owns the content I create?", a: "You do. 100% ownership of all content generated with IDKit." },
    { q: "Is IDKit GDPR compliant?", a: "Yes. GDPR, CCPA, and SOC 2 compliant. Privacy-first architecture." },
  ]},
  { name: "Pricing", icon: "💳", items: [
    { q: "What are the pricing tiers?", a: "Free (limited, watermarked), Creator ($29/mo - full tools), Pro ($79/mo - unlimited, API), Enterprise (custom)." },
    { q: "Is there a free trial?", a: "Yes. 14-day Pro trial. Full features, no credit card required." },
    { q: "Can I cancel anytime?", a: "Yes. No long-term contracts. Cancel anytime, keep your exported content." },
    { q: "Do you offer team plans?", a: "Enterprise plans support teams with shared assets, approval workflows, and brand management." },
  ]},
];

export default function FAQPage() {
  const [search, setSearch] = useState('');
  const [open, setOpen] = useState<Record<string, boolean>>({});
  const filtered = FAQ_DATA.map(cat => ({ ...cat, items: cat.items.filter(i => i.q.toLowerCase().includes(search.toLowerCase()) || i.a.toLowerCase().includes(search.toLowerCase())) })).filter(c => c.items.length > 0);

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="bg-gradient-to-r from-violet-600 to-fuchsia-600 text-white py-16 px-4">
        <div className="max-w-4xl mx-auto text-center">
          <h1 className="text-4xl font-bold mb-4">Help Center</h1>
          <p className="text-xl opacity-90 mb-8">24 answers about AI influencer tools</p>
          <input type="text" placeholder="Search..." value={search} onChange={e => setSearch(e.target.value)} className="w-full max-w-md px-6 py-3 rounded-full text-gray-900" />
        </div>
      </div>
      <div className="max-w-4xl mx-auto py-12 px-4">
        {filtered.map((cat, ci) => (
          <div key={cat.name} className="mb-10">
            <h2 className="text-xl font-semibold mb-4 flex items-center gap-2"><span>{cat.icon}</span>{cat.name}</h2>
            <div className="space-y-3">
              {cat.items.map((faq, fi) => {
                const key = `${ci}-${fi}`;
                return (
                  <div key={key} className="bg-white rounded-lg shadow-sm border overflow-hidden">
                    <button onClick={() => setOpen(p => ({...p, [key]: !p[key]}))} className="w-full p-4 text-left flex justify-between items-center hover:bg-gray-50">
                      <span className="font-medium">{faq.q}</span>
                      <span className={`transition-transform ${open[key] ? 'rotate-180' : ''}`}>▼</span>
                    </button>
                    {open[key] && <div className="px-4 pb-4 text-gray-600 whitespace-pre-line">{faq.a}</div>}
                  </div>
                );
              })}
            </div>
          </div>
        ))}
        <div className="mt-12 bg-gradient-to-r from-violet-600 to-fuchsia-600 rounded-2xl p-8 text-center text-white">
          <h3 className="text-2xl font-bold mb-2">Still have questions?</h3>
          <Link href="mailto:support@idkit.ai" className="inline-block mt-4 px-6 py-3 bg-white text-violet-600 rounded-full font-semibold hover:bg-gray-100">Contact Support</Link>
        </div>
      </div>
    </div>
  );
}
