"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { BottomNav } from "@/components/nav/BottomNav";
import { apiRequest } from "@/lib/api";

type TabType = "all" | "comments" | "mentions" | "messages";

interface Notification {
  id: string;
  type: string;
  user: { name: string; username: string; avatar: string | null };
  content: string;
  post: string | null;
  time: string;
  read: boolean;
}

interface Message {
  id: string;
  user: { name: string; username: string; avatar: string | null };
  lastMessage: string;
  time: string;
  unread: number;
}

export default function InboxPage() {
  const [activeTab, setActiveTab] = useState<TabType>("all");
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchInbox() {
      try {
        const [notifResponse, msgResponse] = await Promise.allSettled([
          apiRequest<Notification[]>("/api/v1/notifications"),
          apiRequest<Message[]>("/api/v1/messages"),
        ]);
        if (notifResponse.status === "fulfilled") {
          setNotifications(Array.isArray(notifResponse.value) ? notifResponse.value : []);
        }
        if (msgResponse.status === "fulfilled") {
          setMessages(Array.isArray(msgResponse.value) ? msgResponse.value : []);
        }
      } catch {
        // silently fail
      } finally {
        setLoading(false);
      }
    }
    fetchInbox();
  }, []);

  const mockNotifications = notifications;
  const mockMessages = messages;

  const unreadCount = mockNotifications.filter((n: Notification) => !n.read).length;

  return (
    <main className="min-h-screen bg-black pb-20">
      {/* Header */}
      <header className="sticky top-0 z-40 bg-black/90 backdrop-blur-sm border-b border-gray-800">
        <div className="flex items-center justify-between px-4 py-3">
          <h1 className="text-xl font-bold text-white">Inbox</h1>
          {unreadCount > 0 && (
            <button className="text-sm text-purple-400 hover:text-purple-300 transition-colors">
              Mark all read
            </button>
          )}
        </div>

        {/* Tabs */}
        <div className="flex border-b border-gray-800">
          {(["all", "comments", "mentions", "messages"] as TabType[]).map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`flex-1 py-3 text-sm font-medium transition-colors relative ${activeTab === tab
                ? "text-white border-b-2 border-purple-500"
                : "text-gray-300"
                }`}
            >
              {tab.charAt(0).toUpperCase() + tab.slice(1)}
              {tab === "messages" && mockMessages.some((m) => m.unread > 0) && (
                <span className="absolute top-2 right-1/4 w-2 h-2 bg-purple-500 rounded-full" />
              )}
            </button>
          ))}
        </div>
      </header>

      {/* Content */}
      {activeTab !== "messages" ? (
        <div className="divide-y divide-gray-800">
          {mockNotifications
            .filter((n) => {
              if (activeTab === "all") return true;
              if (activeTab === "comments") return n.type === "comment";
              if (activeTab === "mentions") return n.type === "mention";
              return true;
            })
            .map((notification) => (
              <Link
                key={notification.id}
                href={`/notifications/${notification.id}`}
                className={`flex gap-3 p-4 hover:bg-gray-900 transition-colors ${!notification.read ? "bg-gray-900/50" : ""
                  }`}
              >
                {/* Avatar */}
                <div className="relative">
                  <div className="w-12 h-12 rounded-full bg-gradient-to-br from-purple-500 via-pink-500 to-orange-500 p-0.5">
                    <div className="w-full h-full rounded-full bg-gray-800 flex items-center justify-center">
                      <span className="text-sm font-bold">
                        {notification.user.name.charAt(0)}
                      </span>
                    </div>
                  </div>
                  {/* Type indicator */}
                  <div className="absolute -bottom-1 -right-1 w-5 h-5 rounded-full bg-gray-900 flex items-center justify-center">
                    {notification.type === "like" && (
                      <HeartIcon className="w-3 h-3 text-red-500" />
                    )}
                    {notification.type === "comment" && (
                      <ChatIcon className="w-3 h-3 text-blue-500" />
                    )}
                    {notification.type === "follow" && (
                      <UserPlusIcon className="w-3 h-3 text-green-500" />
                    )}
                    {notification.type === "mention" && (
                      <AtIcon className="w-3 h-3 text-purple-500" />
                    )}
                    {notification.type === "collab" && (
                      <SparklesIcon className="w-3 h-3 text-yellow-500" />
                    )}
                  </div>
                </div>

                {/* Content */}
                <div className="flex-1 min-w-0">
                  <p className="text-sm">
                    <span className="font-semibold">{notification.user.name}</span>{" "}
                    <span className="text-gray-200">{notification.content}</span>
                  </p>
                  {notification.post && (
                    <p className="text-sm text-gray-300 truncate mt-0.5">
                      {notification.post}
                    </p>
                  )}
                  <p className="text-xs text-gray-300 mt-1">{notification.time}</p>
                </div>

                {/* Unread indicator */}
                {!notification.read && (
                  <div className="w-2 h-2 bg-purple-500 rounded-full self-center" />
                )}
              </Link>
            ))}
        </div>
      ) : (
        <div className="divide-y divide-gray-800">
          {mockMessages.map((message) => (
            <Link
              key={message.id}
              href={`/messages/${message.id}`}
              className="flex gap-3 p-4 hover:bg-gray-900 transition-colors"
            >
              {/* Avatar */}
              <div className="w-12 h-12 rounded-full bg-gradient-to-br from-purple-500 via-pink-500 to-orange-500 p-0.5">
                <div className="w-full h-full rounded-full bg-gray-800 flex items-center justify-center">
                  <span className="text-sm font-bold">
                    {message.user.name.charAt(0)}
                  </span>
                </div>
              </div>

              {/* Content */}
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between">
                  <span className="font-semibold text-sm">{message.user.name}</span>
                  <span className="text-xs text-gray-300">{message.time}</span>
                </div>
                <p className="text-sm text-gray-200 truncate mt-0.5">
                  {message.lastMessage}
                </p>
              </div>

              {/* Unread count */}
              {message.unread > 0 && (
                <div className="w-5 h-5 bg-purple-500 rounded-full flex items-center justify-center self-center">
                  <span className="text-xs font-bold">{message.unread}</span>
                </div>
              )}
            </Link>
          ))}
        </div>
      )}

      {/* Empty State */}
      {mockNotifications.length === 0 && activeTab !== "messages" && (
        <div className="flex flex-col items-center justify-center py-20">
          <div className="w-16 h-16 rounded-full bg-gray-800 flex items-center justify-center mb-4">
            <BellIcon className="w-8 h-8 text-gray-200" />
          </div>
          <h3 className="font-medium text-gray-200">No notifications yet</h3>
          <p className="text-sm text-gray-300 mt-1">
            When you get notifications, they&apos;ll show up here
          </p>
        </div>
      )}

      {/* Smart Reply Suggestion */}
      {activeTab === "comments" && mockNotifications.some((n) => n.type === "comment") && (
        <div className="fixed bottom-24 left-4 right-4 z-30">
          <div className="bg-gradient-to-r from-purple-900/90 to-pink-900/90 backdrop-blur-sm rounded-2xl p-4 border border-purple-500/30">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-full bg-purple-500/30 flex items-center justify-center">
                <SparklesIcon className="w-5 h-5 text-purple-400" />
              </div>
              <div className="flex-1">
                <h4 className="font-medium text-sm">Smart Reply Available</h4>
                <p className="text-xs text-gray-300">
                  AI can help you respond to 3 comments
                </p>
              </div>
              <Link
                href="/inbox/smart-reply"
                className="px-4 py-2 bg-purple-600 rounded-lg text-sm font-medium hover:bg-purple-700 transition-colors"
              >
                Reply
              </Link>
            </div>
          </div>
        </div>
      )}

      <BottomNav />
    </main>
  );
}

// Icons
function HeartIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor">
      <path d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
    </svg>
  );
}

function ChatIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor">
      <path d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
    </svg>
  );
}

function UserPlusIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor">
      <path d="M8 7a4 4 0 118 0 4 4 0 01-8 0zm0 10a6 6 0 1012 0v1H8v-1zm10-8h4m-2-2v4" />
    </svg>
  );
}

function AtIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
      <circle cx="12" cy="12" r="4" />
      <path d="M16 8v5a3 3 0 006 0v-1a10 10 0 10-3.92 7.94" />
    </svg>
  );
}

function SparklesIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor">
      <path d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z" />
    </svg>
  );
}

function BellIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
    </svg>
  );
}
