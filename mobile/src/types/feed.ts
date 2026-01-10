/**
 * Feed Types
 */

export interface Post {
  id: string;
  user_id: string;
  post_type: 'video' | 'image' | 'text' | 'carousel' | 'podcast_clip';
  content_text?: string;
  media_urls: string[];
  thumbnail_url?: string;

  // Engagement metrics
  view_count: number;
  like_count: number;
  comment_count: number;
  share_count: number;
  save_count: number;

  // User interactions
  is_liked: boolean;
  is_saved: boolean;
  is_following_author: boolean;

  // Author info
  author: {
    id: string;
    username: string;
    display_name: string;
    avatar_url?: string;
    is_verified: boolean;
  };

  // Content metadata
  hashtags: string[];
  mentions: string[];
  audio_info?: {
    id: string;
    name: string;
    artist: string;
  };

  // Timestamps
  created_at: string;
  updated_at: string;
}

export interface Comment {
  id: string;
  post_id: string;
  user_id: string;
  content: string;
  like_count: number;
  reply_count: number;
  is_liked: boolean;
  author: {
    id: string;
    username: string;
    display_name: string;
    avatar_url?: string;
  };
  created_at: string;
}
