"use client";

import { useState } from "react";
import { ArrowLeft, Image as ImageIcon, Send, Loader2 } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";

export default function CreatePostPage() {
  const [content, setContent] = useState("");
  const [isPosting, setIsPosting] = useState(false);
  const router = useRouter();

  const handlePost = async () => {
    if (!content.trim()) return;
    
    setIsPosting(true);
    try {
      const token = localStorage.getItem("access_token");
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/feed/posts`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token && { Authorization: `Bearer ${token}` }),
        },
        body: JSON.stringify({
          post_type: "text",
          content_text: content,
          visibility: "public",
        }),
      });

      if (response.ok) {
        router.push("/");
      } else {
        alert("Failed to create post. Please try again.");
      }
    } catch (error) {
      console.error("Post error:", error);
      alert("Failed to create post. Please try again.");
    } finally {
      setIsPosting(false);
    }
  };

  return (
    <div className="min-h-screen bg-black text-white">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-gray-800">
        <Link href="/" className="p-2 hover:bg-gray-800 rounded-full">
          <ArrowLeft className="w-6 h-6" />
        </Link>
        <h1 className="text-lg font-semibold">Create Post</h1>
        <button
          onClick={handlePost}
          disabled={!content.trim() || isPosting}
          className="px-4 py-2 bg-gradient-to-r from-purple-500 to-pink-500 rounded-full font-semibold disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
        >
          {isPosting ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : (
            <Send className="w-4 h-4" />
          )}
          Post
        </button>
      </div>

      {/* Content Area */}
      <div className="p-4">
        <textarea
          value={content}
          onChange={(e) => setContent(e.target.value)}
          placeholder="What's on your mind?"
          className="w-full h-64 bg-transparent text-lg resize-none focus:outline-none placeholder-gray-500"
          autoFocus
        />
      </div>

      {/* Media Options */}
      <div className="fixed bottom-0 left-0 right-0 p-4 border-t border-gray-800 bg-black">
        <div className="flex items-center gap-4">
          <button className="p-3 hover:bg-gray-800 rounded-full">
            <ImageIcon className="w-6 h-6 text-gray-400" />
          </button>
          <span className="text-gray-500 text-sm">
            {content.length}/2000 characters
          </span>
        </div>
      </div>
    </div>
  );
}
