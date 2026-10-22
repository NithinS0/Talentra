"use client";

import { useEffect, useState } from "react";
import { DashboardShell } from "@/components/layout/dashboard-shell";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  LifeBuoy,
  HelpCircle,
  Share2,
  AlertCircle,
  CheckCircle2,
  Loader2,
  PlusCircle,
  FileQuestion,
  Search,
} from "lucide-react";
import {
  createSupportTicket,
  getSupportTicket,
  getFaqs,
  recordReferral,
} from "@/lib/api/notifications";
import {
  SupportTicketResponse,
  FaqResponse,
  ReferralEventResponse,
} from "@/types/notifications";
import { formatDate } from "@/lib/utils";

export default function SupportPage() {
  const [faqs, setFaqs] = useState<FaqResponse[]>([]);
  const [isLoadingFaqs, setIsLoadingFaqs] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  // Support Ticket Form State
  const [ticketSubject, setTicketSubject] = useState<string>("");
  const [ticketDescription, setTicketDescription] = useState<string>("");
  const [ticketPriority, setTicketPriority] = useState<number>(2);
  const [isSubmittingTicket, setIsSubmittingTicket] = useState<boolean>(false);
  const [recentTicket, setRecentTicket] = useState<SupportTicketResponse | null>(null);

  // Ticket Lookup State
  const [lookupTicketId, setLookupTicketId] = useState<string>("");
  const [lookedUpTicket, setLookedUpTicket] = useState<SupportTicketResponse | null>(null);
  const [isLookingUp, setIsLookingUp] = useState<boolean>(false);

  // Referral State (FR-0148)
  const [referralCode, setReferralCode] = useState<string>("TALENTRA2026");
  const [refereeUserId, setRefereeUserId] = useState<string>("2");
  const [isRecordingReferral, setIsRecordingReferral] = useState<boolean>(false);
  const [referralResult, setReferralResult] = useState<ReferralEventResponse | null>(null);

  useEffect(() => {
    let isMounted = true;
    async function loadFaqs() {
      try {
        setIsLoadingFaqs(true);
        const res = await getFaqs(true);
        if (isMounted) setFaqs(res || []);
      } catch (err: unknown) {
        if (isMounted) setError(err instanceof Error ? err.message : "Failed to load FAQs");
      } finally {
        if (isMounted) setIsLoadingFaqs(false);
      }
    }
    loadFaqs();
    return () => {
      isMounted = false;
    };
  }, []);

  const handleCreateTicket = async (e: React.FormEvent) => {
    e.preventDefault();
    if (ticketSubject.length < 5 || ticketDescription.length < 10) {
      setError("Subject must be at least 5 chars and description at least 10 chars.");
      return;
    }

    try {
      setIsSubmittingTicket(true);
      setError(null);
      const res = await createSupportTicket({
        subject: ticketSubject,
        description: ticketDescription,
        priority_code_id: ticketPriority,
      });
      setRecentTicket(res);
      setSuccessMessage(`Support ticket '${res.ticket_number}' created successfully.`);
      setTicketSubject("");
      setTicketDescription("");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to submit support ticket");
    } finally {
      setIsSubmittingTicket(false);
    }
  };

  const handleLookupTicket = async (e: React.FormEvent) => {
    e.preventDefault();
    const tId = parseInt(lookupTicketId, 10);
    if (isNaN(tId) || tId <= 0) {
      setError("Please provide a valid ticket ID.");
      return;
    }

    try {
      setIsLookingUp(true);
      setError(null);
      const res = await getSupportTicket(tId);
      setLookedUpTicket(res);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : `Access denied or ticket #${tId} not found (FR-0146).`);
      setLookedUpTicket(null);
    } finally {
      setIsLookingUp(false);
    }
  };

  const handleRecordReferral = async (e: React.FormEvent) => {
    e.preventDefault();
    const refereeId = parseInt(refereeUserId, 10);
    if (isNaN(refereeId) || refereeId <= 0) {
      setError("Please specify a valid referee user ID.");
      return;
    }

    try {
      setIsRecordingReferral(true);
      setError(null);
      const res = await recordReferral({
        referrer_user_id: 1,
        referee_user_id: refereeId,
        referral_code: referralCode,
        event_type: "SIGNUP",
      });
      setReferralResult(res);
      setSuccessMessage(`Referral event #${res.id} attributed without duplicate credit (FR-0148).`);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to record referral event");
    } finally {
      setIsRecordingReferral(false);
    }
  };

  const getPriorityBadge = (codeId: number) => {
    switch (codeId) {
      case 1:
        return <Badge variant="outline">LOW</Badge>;
      case 2:
        return <Badge variant="default">MEDIUM</Badge>;
      case 3:
        return <Badge variant="warning">HIGH</Badge>;
      case 4:
        return <Badge variant="destructive">URGENT</Badge>;
      default:
        return <Badge variant="outline">NORMAL</Badge>;
    }
  };

  return (
    <DashboardShell
      title="Support Tickets, FAQs & Referrals"
      breadcrumbs={[{ label: "Support" }]}
    >
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
            Support Centre & FAQs (Module M10)
          </h1>
          <p className="text-sm text-slate-500 dark:text-slate-400">
            Submit customer support tickets, search active FAQs, and manage referral attributions.
          </p>
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
          {/* Create Support Ticket Form */}
          <Card className="lg:col-span-1">
            <CardHeader>
              <CardTitle className="text-base flex items-center gap-2">
                <LifeBuoy className="w-4 h-4 text-primary" />
                Submit Support Ticket
              </CardTitle>
              <CardDescription>
                Direct routing to authorized support agents.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleCreateTicket} className="space-y-4">
                <div>
                  <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                    Ticket Subject
                  </label>
                  <input
                    type="text"
                    placeholder="e.g. Issue with seat allocation capacity"
                    value={ticketSubject}
                    onChange={(e) => setTicketSubject(e.target.value)}
                    className="w-full px-3 py-2 text-sm border border-slate-300 dark:border-slate-700 rounded-md bg-white dark:bg-slate-900 text-slate-900 dark:text-white"
                    required
                  />
                </div>

                <div>
                  <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                    Priority
                  </label>
                  <select
                    value={ticketPriority}
                    onChange={(e) => setTicketPriority(parseInt(e.target.value, 10))}
                    className="w-full px-3 py-2 text-sm border border-slate-300 dark:border-slate-700 rounded-md bg-white dark:bg-slate-900 text-slate-900 dark:text-white"
                  >
                    <option value={1}>Low</option>
                    <option value={2}>Medium</option>
                    <option value={3}>High</option>
                    <option value={4}>Urgent</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                    Detailed Description
                  </label>
                  <textarea
                    rows={4}
                    placeholder="Explain the technical or account issue in detail..."
                    value={ticketDescription}
                    onChange={(e) => setTicketDescription(e.target.value)}
                    className="w-full px-3 py-2 text-sm border border-slate-300 dark:border-slate-700 rounded-md bg-white dark:bg-slate-900 text-slate-900 dark:text-white"
                    required
                  />
                </div>

                <Button
                  type="submit"
                  variant="primary"
                  disabled={isSubmittingTicket}
                  className="w-full flex items-center justify-center gap-2"
                >
                  {isSubmittingTicket ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <PlusCircle className="w-4 h-4" />
                  )}
                  Submit Ticket
                </Button>
              </form>
            </CardContent>
          </Card>

          {/* Ticket Lookup & Ownership Verification (FR-0146) */}
          <div className="lg:col-span-2 space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="text-base flex items-center gap-2">
                  <Search className="w-4 h-4 text-primary" />
                  Ticket Ownership Verification (FR-0146)
                </CardTitle>
                <CardDescription>
                  Access is strictly limited to the ticket requester or authorized support administrators.
                </CardDescription>
              </CardHeader>
              <CardContent>
                <form onSubmit={handleLookupTicket} className="flex gap-3 max-w-md">
                  <input
                    type="number"
                    placeholder="Enter Ticket ID (e.g. 1)"
                    value={lookupTicketId}
                    onChange={(e) => setLookupTicketId(e.target.value)}
                    className="w-full px-3 py-2 text-sm border border-slate-300 dark:border-slate-700 rounded-md bg-white dark:bg-slate-900 text-slate-900 dark:text-white"
                    min="1"
                    required
                  />
                  <Button type="submit" variant="primary" disabled={isLookingUp}>
                    {isLookingUp ? <Loader2 className="w-4 h-4 animate-spin" /> : "Verify Access"}
                  </Button>
                </form>

                {lookedUpTicket && (
                  <div className="mt-4 p-4 border border-slate-200 dark:border-slate-800 rounded-lg space-y-3">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-slate-900 dark:text-white">
                          {lookedUpTicket.ticket_number}
                        </span>
                        {getPriorityBadge(lookedUpTicket.priority_code_id)}
                      </div>
                      <span className="text-xs text-slate-400">
                        {formatDate(lookedUpTicket.created_at)}
                      </span>
                    </div>
                    <h4 className="text-sm font-semibold">{lookedUpTicket.subject}</h4>
                    <p className="text-xs text-slate-600 dark:text-slate-300">
                      {lookedUpTicket.description}
                    </p>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Public FAQs (FR-0147) */}
            <Card>
              <CardHeader>
                <CardTitle className="text-base flex items-center gap-2">
                  <HelpCircle className="w-4 h-4 text-emerald-500" />
                  Frequently Asked Questions (Published FAQs)
                </CardTitle>
                <CardDescription>
                  Public queries strictly filter out draft or inactive entries (FR-0147).
                </CardDescription>
              </CardHeader>
              <CardContent>
                {isLoadingFaqs ? (
                  <div className="flex items-center justify-center py-8">
                    <Loader2 className="w-5 h-5 animate-spin text-primary" />
                  </div>
                ) : faqs.length === 0 ? (
                  <div className="py-8 text-center text-slate-500 text-sm">
                    No active FAQs currently published.
                  </div>
                ) : (
                  <div className="space-y-4">
                    {faqs.map((faq) => (
                      <div
                        key={faq.id}
                        className="p-4 border border-slate-100 dark:border-slate-800 rounded-lg space-y-1.5"
                      >
                        <h4 className="font-semibold text-slate-900 dark:text-white text-sm">
                          {faq.name || `Question #${faq.id}`}
                        </h4>
                        <p className="text-xs text-slate-600 dark:text-slate-300 leading-relaxed">
                          {faq.description || "Details available in published documentation."}
                        </p>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Referral Attribution (FR-0148) */}
            <Card>
              <CardHeader>
                <CardTitle className="text-base flex items-center gap-2">
                  <Share2 className="w-4 h-4 text-indigo-500" />
                  Referral Program Attribution (FR-0148)
                </CardTitle>
                <CardDescription>
                  Valid referrals are recorded once without duplicate attribution credit.
                </CardDescription>
              </CardHeader>
              <CardContent>
                <form onSubmit={handleRecordReferral} className="flex flex-col sm:flex-row gap-3">
                  <input
                    type="text"
                    placeholder="Referral Code"
                    value={referralCode}
                    onChange={(e) => setReferralCode(e.target.value)}
                    className="w-full sm:w-1/2 px-3 py-2 text-sm border border-slate-300 dark:border-slate-700 rounded-md bg-white dark:bg-slate-900 text-slate-900 dark:text-white"
                    required
                  />
                  <input
                    type="number"
                    placeholder="Referee User ID"
                    value={refereeUserId}
                    onChange={(e) => setRefereeUserId(e.target.value)}
                    className="w-full sm:w-1/3 px-3 py-2 text-sm border border-slate-300 dark:border-slate-700 rounded-md bg-white dark:bg-slate-900 text-slate-900 dark:text-white"
                    min="1"
                    required
                  />
                  <Button
                    type="submit"
                    variant="outline"
                    disabled={isRecordingReferral}
                    className="text-xs flex items-center gap-1.5 whitespace-nowrap"
                  >
                    {isRecordingReferral ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Share2 className="w-3.5 h-3.5" />}
                    Attribute
                  </Button>
                </form>

                {referralResult && (
                  <div className="mt-3 text-xs text-emerald-600 dark:text-emerald-400 font-medium">
                    Referral Event #{referralResult.id} confirmed at {formatDate(referralResult.occurred_at)}.
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </DashboardShell>
  );
}
