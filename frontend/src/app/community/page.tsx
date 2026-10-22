"use client";

import { useState } from "react";
import { DashboardShell } from "@/components/layout/dashboard-shell";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  MessageSquare,
  ThumbsUp,
  Sparkles,
  AlertCircle,
  CheckCircle2,
  Loader2,
  Send,
  HelpCircle,
} from "lucide-react";
import {
  createCommunityPost,
  reactToCommunityPost,
} from "@/lib/api/notifications";
import {
  CommunityPostResponse,
} from "@/types/notifications";
import { formatDate } from "@/lib/utils";

export default function CommunityPage() {
  const [posts, setPosts] = useState<CommunityPostResponse[]>([
    {
      id: 1,
      author_user_id: 1,
      title: "Best Practices for Modern FastAPI + Supabase Full-Stack Architecture",
      body: "When building scalable recruitment pipelines, always ensure append-only audit ledgers and strict zero-PII storage. Never persist raw identity documents in transactional databases.",
      language_id: 1,
      moderation_status_code_id: 1,
      created_at: "2026-10-21T08:00:00Z",
      updated_at: "2026-10-21T08:00:00Z",
    },
    {
      id: 2,
      author_user_id: 2,
      title: "Preparing for Campus Placement Drives: A Guide for TPOs and Students",
      body: "Institutional verification through DigiLocker ensures automated verification with minimal administrative turnaround. Check out our Stage 14 integration boundary register for details.",
      language_id: 1,
      moderation_status_code_id: 1,
      created_at: "2026-10-20T12:00:00Z",
      updated_at: "2026-10-20T12:00:00Z",
    },
  ]);

  const [postTitle, setPostTitle] = useState<string>("");
  const [postBody, setPostBody] = useState<string>("");
  const [postLang, setPostLang] = useState<string>("en");
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  // Reactions count map: `${postId}-${reactionType}` -> count
  const [reactions, setReactions] = useState<Record<string, number>>({
    "1-LIKE": 12,
    "1-HELPFUL": 7,
    "2-LIKE": 5,
    "2-INSIGHTFUL": 3,
  });

  const handleCreatePost = async (e: React.FormEvent) => {
    e.preventDefault();
    if (postTitle.length < 3 || postBody.length < 1) {
      setError("Please provide a valid title and body.");
      return;
    }
    if (postBody.length > 10000) {
      setError("Post body exceeds 10,000 character maximum boundary (FR-0144).");
      return;
    }

    try {
      setIsSubmitting(true);
      setError(null);
      const res = await createCommunityPost({
        title: postTitle,
        body: postBody,
        language_code: postLang,
      });

      setPosts((prev) => [res, ...prev]);
      setSuccessMessage(`Community post '#${res.id}: ${res.title}' published successfully.`);
      setPostTitle("");
      setPostBody("");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to publish community post");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleToggleReaction = async (postId: number, reactionType: string) => {
    try {
      setError(null);
      await reactToCommunityPost(postId, reactionType);
      const key = `${postId}-${reactionType}`;
      setReactions((prev) => ({
        ...prev,
        [key]: (prev[key] || 0) + 1,
      }));
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Reaction update failed");
    }
  };

  return (
    <DashboardShell
      title="Community & Knowledge Sharing"
      breadcrumbs={[{ label: "Community" }]}
    >
      <div className="space-y-6">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
              Community Feed & Discussions (FR-0144, FR-0145)
            </h1>
            <p className="text-sm text-slate-500 dark:text-slate-400">
              Share recruitment knowledge, campus placement insights, and peer guidance.
            </p>
          </div>
        </div>

        {error && (
          <div className="p-4 bg-red-50 dark:bg-red-950/30 border border-red-200 dark:border-red-900 rounded-lg flex items-center justify-between text-red-700 dark:text-red-400">
            <div className="flex items-center gap-3">
              <AlertCircle className="w-5 h-5 flex-shrink-0" />
              <span className="text-sm font-medium">{error}</span>
            </div>
            <button onClick={() => setError(null)} className="text-xs underline">
              Dismiss
            </button>
          </div>
        )}

        {successMessage && (
          <div className="p-4 bg-emerald-50 dark:bg-emerald-950/30 border border-emerald-200 dark:border-emerald-900 rounded-lg flex items-center justify-between text-emerald-700 dark:text-emerald-400">
            <div className="flex items-center gap-3">
              <CheckCircle2 className="w-5 h-5 flex-shrink-0" />
              <span className="text-sm font-medium">{successMessage}</span>
            </div>
            <button onClick={() => setSuccessMessage(null)} className="text-xs underline">
              Dismiss
            </button>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Post Creation Form */}
          <Card className="lg:col-span-1">
            <CardHeader>
              <CardTitle className="text-base flex items-center gap-2">
                <MessageSquare className="w-4 h-4 text-primary" />
                Publish Discussion Post
              </CardTitle>
              <CardDescription>
                UTF-8 encoded free text up to 10,000 characters (FR-0144).
              </CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleCreatePost} className="space-y-4">
                <div>
                  <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                    Post Title
                  </label>
                  <input
                    type="text"
                    placeholder="e.g. Tips for technical interview prep"
                    value={postTitle}
                    onChange={(e) => setPostTitle(e.target.value)}
                    className="w-full px-3 py-2 text-sm border border-slate-300 dark:border-slate-700 rounded-md bg-white dark:bg-slate-900 text-slate-900 dark:text-white"
                    required
                  />
                </div>

                <div>
                  <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                    Language
                  </label>
                  <select
                    value={postLang}
                    onChange={(e) => setPostLang(e.target.value)}
                    className="w-full px-3 py-2 text-sm border border-slate-300 dark:border-slate-700 rounded-md bg-white dark:bg-slate-900 text-slate-900 dark:text-white"
                  >
                    <option value="en">English (en)</option>
                    <option value="hi">Hindi (hi)</option>
                    <option value="es">Spanish (es)</option>
                  </select>
                </div>

                <div>
                  <div className="flex justify-between items-center mb-1">
                    <label className="text-xs font-medium text-slate-700 dark:text-slate-300">
                      Content Body
                    </label>
                    <span className="text-[10px] text-slate-400">
                      {postBody.length} / 10,000
                    </span>
                  </div>
                  <textarea
                    rows={6}
                    placeholder="Share guidance, experience, or discussion questions..."
                    value={postBody}
                    onChange={(e) => setPostBody(e.target.value)}
                    maxLength={10000}
                    className="w-full px-3 py-2 text-sm border border-slate-300 dark:border-slate-700 rounded-md bg-white dark:bg-slate-900 text-slate-900 dark:text-white"
                    required
                  />
                </div>

                <Button
                  type="submit"
                  variant="primary"
                  disabled={isSubmitting}
                  className="w-full flex items-center justify-center gap-2"
                >
                  {isSubmitting ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <Send className="w-4 h-4" />
                  )}
                  Publish to Community
                </Button>
              </form>
            </CardContent>
          </Card>

          {/* Posts Feed */}
          <div className="lg:col-span-2 space-y-4">
            {posts.map((post) => (
              <Card key={post.id} className="hover:border-slate-300 dark:hover:border-slate-700 transition-colors">
                <CardHeader>
                  <div className="flex items-start justify-between gap-4">
                    <div>
                      <CardTitle className="text-lg font-bold text-slate-900 dark:text-white">
                        {post.title}
                      </CardTitle>
                      <CardDescription className="text-xs mt-1">
                        Posted by Author #{post.author_user_id} • {formatDate(post.created_at)}
                      </CardDescription>
                    </div>
                    <Badge variant="outline">{post.language_id ? "en" : "default"}</Badge>
                  </div>
                </CardHeader>
                <CardContent className="space-y-4">
                  <p className="text-sm text-slate-700 dark:text-slate-300 leading-relaxed whitespace-pre-line">
                    {post.body}
                  </p>

                  <div className="flex items-center gap-2 pt-3 border-t border-slate-100 dark:border-slate-800">
                    <Button
                      variant="outline"
                      onClick={() => handleToggleReaction(post.id, "LIKE")}
                      className="h-8 px-2.5 text-xs flex items-center gap-1.5"
                    >
                      <ThumbsUp className="w-3.5 h-3.5 text-blue-500" />
                      <span>Like</span>
                      <span className="font-semibold text-slate-500">
                        {reactions[`${post.id}-LIKE`] || 0}
                      </span>
                    </Button>

                    <Button
                      variant="outline"
                      onClick={() => handleToggleReaction(post.id, "HELPFUL")}
                      className="h-8 px-2.5 text-xs flex items-center gap-1.5"
                    >
                      <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" />
                      <span>Helpful</span>
                      <span className="font-semibold text-slate-500">
                        {reactions[`${post.id}-HELPFUL`] || 0}
                      </span>
                    </Button>

                    <Button
                      variant="outline"
                      onClick={() => handleToggleReaction(post.id, "INSIGHTFUL")}
                      className="h-8 px-2.5 text-xs flex items-center gap-1.5"
                    >
                      <Sparkles className="w-3.5 h-3.5 text-amber-500" />
                      <span>Insightful</span>
                      <span className="font-semibold text-slate-500">
                        {reactions[`${post.id}-INSIGHTFUL`] || 0}
                      </span>
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </div>
    </DashboardShell>
  );
}
