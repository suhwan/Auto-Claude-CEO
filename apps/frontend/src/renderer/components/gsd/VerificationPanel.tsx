/**
 * VerificationPanel Component
 *
 * Manual verification panel for UAT (User Acceptance Testing).
 * Displays checklist items from success_criteria and allows Approve/Reject.
 */

import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Card, CardContent, CardHeader, CardTitle, CardFooter } from '../ui/card';
import { Button } from '../ui/button';
import { Checkbox } from '../ui/checkbox';
import { Textarea } from '../ui/textarea';
import { Badge } from '../ui/badge';
import { Alert, AlertDescription } from '../ui/alert';
import {
  CheckCircle2,
  XCircle,
  AlertCircle,
  Eye,
  Loader2,
  ThumbsUp,
  ThumbsDown
} from 'lucide-react';
import { cn } from '../../lib/utils';
import type {
  GsdPlanVerification,
  GsdVerificationItem,
  VerificationStatus
} from '../../../preload/api/modules/gsd-api';

interface VerificationPanelProps {
  verification: GsdPlanVerification;
  onApprove: (
    planId: string,
    feedback?: string,
    checklist?: GsdVerificationItem[]
  ) => Promise<void>;
  onReject: (
    planId: string,
    feedback: string,
    checklist?: GsdVerificationItem[]
  ) => Promise<void>;
}

export function VerificationPanel({
  verification,
  onApprove,
  onReject
}: VerificationPanelProps) {
  const { t } = useTranslation(['navigation', 'common']);
  const [checklist, setChecklist] = useState<GsdVerificationItem[]>(
    verification.checklist
  );
  const [feedback, setFeedback] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const allChecked = checklist.every((item) => item.checked);

  const toggleItem = (id: string) => {
    setChecklist((prev) =>
      prev.map((item) =>
        item.id === id ? { ...item, checked: !item.checked } : item
      )
    );
  };

  const handleApprove = async () => {
    setSubmitting(true);
    setError(null);
    try {
      await onApprove(verification.plan_id, feedback || undefined, checklist);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to approve');
    } finally {
      setSubmitting(false);
    }
  };

  const handleReject = async () => {
    if (!feedback.trim()) {
      setError(t('navigation:gsd.provideFeedback'));
      return;
    }
    setSubmitting(true);
    setError(null);
    try {
      await onReject(verification.plan_id, feedback, checklist);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to reject');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Card className="border-blue-200 bg-blue-50/30 dark:bg-blue-950/20 dark:border-blue-800">
      <CardHeader className="pb-3">
        <CardTitle className="text-sm flex items-center justify-between">
          <span className="flex items-center gap-2">
            <Eye className="h-4 w-4 text-blue-500" />
            {t('navigation:gsd.manualVerificationRequired')}
          </span>
          <Badge variant="outline" className="text-xs">
            {verification.plan_id}
          </Badge>
        </CardTitle>
        <p className="text-xs text-muted-foreground">{verification.plan_name}</p>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Auto QA Status */}
        <div className="flex items-center gap-2 text-xs">
          {verification.auto_qa_passed ? (
            <>
              <CheckCircle2 className="h-4 w-4 text-green-500" />
              <span className="text-green-700 dark:text-green-400">
                {t('navigation:gsd.autoQaPassed')}
              </span>
            </>
          ) : (
            <>
              <AlertCircle className="h-4 w-4 text-yellow-500" />
              <span className="text-yellow-700 dark:text-yellow-400">
                {t('navigation:gsd.autoQaPending')}
              </span>
            </>
          )}
        </div>

        {/* Checklist */}
        <div className="space-y-2">
          <p className="text-xs font-medium">
            {t('navigation:gsd.verificationChecklist')}:
          </p>
          {checklist.map((item) => (
            <div
              key={item.id}
              className="flex items-start gap-2 p-2 rounded bg-background"
            >
              <Checkbox
                id={`check-${item.id}`}
                checked={item.checked}
                onCheckedChange={() => toggleItem(item.id)}
                className="mt-0.5"
              />
              <label
                htmlFor={`check-${item.id}`}
                className={cn(
                  'text-xs cursor-pointer flex-1',
                  item.checked && 'line-through text-muted-foreground'
                )}
              >
                {item.description}
              </label>
            </div>
          ))}
        </div>

        {/* Feedback */}
        <div className="space-y-2">
          <p className="text-xs font-medium">
            {allChecked
              ? t('navigation:gsd.feedbackOptional')
              : t('navigation:gsd.feedbackRequired')}
            :
          </p>
          <Textarea
            placeholder={t('navigation:gsd.feedbackPlaceholder')}
            value={feedback}
            onChange={(e) => setFeedback(e.target.value)}
            className="text-xs min-h-[80px]"
          />
        </div>

        {/* Error */}
        {error && (
          <Alert variant="destructive" className="py-2">
            <AlertDescription className="text-xs">{error}</AlertDescription>
          </Alert>
        )}
      </CardContent>

      <CardFooter className="flex justify-end gap-2 pt-0">
        <Button
          variant="outline"
          size="sm"
          onClick={handleReject}
          disabled={submitting}
          className="text-red-600 hover:text-red-700 hover:bg-red-50 dark:text-red-400 dark:hover:text-red-300 dark:hover:bg-red-950"
        >
          {submitting ? (
            <Loader2 className="h-4 w-4 animate-spin mr-1" />
          ) : (
            <ThumbsDown className="h-4 w-4 mr-1" />
          )}
          {t('navigation:gsd.reject')}
        </Button>
        <Button
          size="sm"
          onClick={handleApprove}
          disabled={submitting || !allChecked}
          className="bg-green-600 hover:bg-green-700 dark:bg-green-700 dark:hover:bg-green-600"
        >
          {submitting ? (
            <Loader2 className="h-4 w-4 animate-spin mr-1" />
          ) : (
            <ThumbsUp className="h-4 w-4 mr-1" />
          )}
          {t('navigation:gsd.approve')}
        </Button>
      </CardFooter>
    </Card>
  );
}

/**
 * Compact verification badge for plan list
 */
interface VerificationBadgeProps {
  status: VerificationStatus;
  onClick?: () => void;
}

export function VerificationBadge({ status, onClick }: VerificationBadgeProps) {
  const { t } = useTranslation(['navigation']);

  const config = {
    pending: {
      icon: Eye,
      text: t('navigation:gsd.needsReview'),
      className: 'bg-blue-100 text-blue-700 border-blue-300 dark:bg-blue-950 dark:text-blue-300 dark:border-blue-700'
    },
    approved: {
      icon: CheckCircle2,
      text: t('navigation:gsd.approved'),
      className: 'bg-green-100 text-green-700 border-green-300 dark:bg-green-950 dark:text-green-300 dark:border-green-700'
    },
    rejected: {
      icon: XCircle,
      text: t('navigation:gsd.rejected'),
      className: 'bg-red-100 text-red-700 border-red-300 dark:bg-red-950 dark:text-red-300 dark:border-red-700'
    },
    not_required: {
      icon: CheckCircle2,
      text: t('navigation:gsd.autoQa'),
      className: 'bg-gray-100 text-gray-700 border-gray-300 dark:bg-gray-800 dark:text-gray-300 dark:border-gray-600'
    }
  };

  const { icon: Icon, text, className } = config[status];

  return (
    <Badge
      variant="outline"
      className={cn('text-[10px] cursor-pointer', className)}
      onClick={onClick}
    >
      <Icon className="h-3 w-3 mr-1" />
      {text}
    </Badge>
  );
}
