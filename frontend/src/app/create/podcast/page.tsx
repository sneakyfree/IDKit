import Link from "next/link";
import { ArrowLeft, Mic } from "lucide-react";

export default function CreatePodcastPage() {
  return (
    <div className="min-h-screen bg-black text-white flex flex-col items-center justify-center p-4">
      <Link href="/" className="absolute top-4 left-4 p-2 hover:bg-gray-800 rounded-full">
        <ArrowLeft className="w-6 h-6" />
      </Link>
      <Mic className="w-16 h-16 text-orange-500 mb-4" />
      <h1 className="text-2xl font-bold mb-2">Podcast Creation</h1>
      <p className="text-gray-400 text-center">Coming soon! Record or generate podcast episodes.</p>
    </div>
  );
}
