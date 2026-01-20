import { useState, useEffect, useRef } from 'react';
import { useTranslation } from 'react-i18next';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '../ui/dialog';
import { Button } from '../ui/button';
import { Textarea } from '../ui/textarea';
import { Label } from '../ui/label';
import { Progress } from '../ui/progress';
import { ScrollArea } from '../ui/scroll-area';
import { Loader2, FileText, X } from 'lucide-react';
import { Alert, AlertDescription } from '../ui/alert';

interface PlanPhaseDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  projectPath: string;
  phaseNumber: number;
  phaseGoal: string;
  onPlanCreated: () => void;
}

export function PlanPhaseDialog({
  open,
  onOpenChange,
  projectPath,
  phaseNumber,
  phaseGoal,
  onPlanCreated
}: PlanPhaseDialogProps) {
  const { t } = useTranslation(['navigation', 'common']);
  const [additionalContext, setAdditionalContext] = useState('');
  const [generating, setGenerating] = useState(false);
  const [output, setOutput] = useState<string[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [progress, setProgress] = useState(0);
  const [generatorId, setGeneratorId] = useState<string | null>(null);
  const outputRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!generating || !generatorId) return;

    const unsubOutput = window.electronAPI.gsd.onPlanOutput?.((data) => {
      if (data.generatorId === generatorId) {
        setOutput(prev => [...prev, data.data]);
      }
    });

    const unsubProgress = window.electronAPI.gsd.onPlanProgress?.((data) => {
      if (data.generatorId === generatorId) {
        setProgress(Math.round((data.current / data.total) * 100));
      }
    });

    const unsubError = window.electronAPI.gsd.onPlanError?.((data) => {
      if (data.generatorId === generatorId) {
        setError(data.error);
      }
    });

    const unsubComplete = window.electronAPI.gsd.onPlanComplete?.((data) => {
      if (data.generatorId === generatorId) {
        setGenerating(false);
        setProgress(100);
        if (data.success) {
          setTimeout(() => {
            onPlanCreated();
            handleClose();
          }, 500);
        }
      }
    });

    return () => {
      unsubOutput?.();
      unsubProgress?.();
      unsubError?.();
      unsubComplete?.();
    };
  }, [generating, generatorId, onPlanCreated]);

  useEffect(() => {
    if (outputRef.current) {
      outputRef.current.scrollTop = outputRef.current.scrollHeight;
    }
  }, [output]);

  const handleGenerate = async () => {
    setGenerating(true);
    setOutput([]);
    setError(null);
    setProgress(0);

    try {
      const result = await window.electronAPI.gsd.planPhase(projectPath, {
        phaseNumber,
        additionalContext: additionalContext.trim() || undefined
      });

      if (result.success && result.data) {
        setGeneratorId(result.data.generatorId);
      } else {
        setError(result.error || t('navigation:gsd.planPhaseFailed'));
        setGenerating(false);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : t('navigation:gsd.planPhaseFailed'));
      setGenerating(false);
    }
  };

  const handleCancel = async () => {
    if (generatorId) {
      await window.electronAPI.gsd.cancelPlan(generatorId);
    }
    setGenerating(false);
    setGeneratorId(null);
  };

  const handleClose = () => {
    if (generating) {
      handleCancel();
    }
    setAdditionalContext('');
    setOutput([]);
    setError(null);
    setProgress(0);
    setGeneratorId(null);
    onOpenChange(false);
  };

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-[600px]">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <FileText className="h-5 w-5" />
            {t('navigation:gsd.planPhase')} {phaseNumber}
          </DialogTitle>
          <DialogDescription>
            {t('navigation:gsd.planPhaseDescription')}
          </DialogDescription>
        </DialogHeader>

        {!generating ? (
          <>
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label>{t('navigation:gsd.phaseGoal')}</Label>
                <div className="p-3 rounded bg-muted text-sm">
                  {phaseGoal}
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="context">{t('navigation:gsd.additionalContext')}</Label>
                <Textarea
                  id="context"
                  value={additionalContext}
                  onChange={(e) => setAdditionalContext(e.target.value)}
                  placeholder={t('navigation:gsd.additionalContextPlaceholder')}
                  rows={3}
                />
                <p className="text-xs text-muted-foreground">
                  {t('navigation:gsd.additionalContextHint')}
                </p>
              </div>

              {error && (
                <Alert variant="destructive">
                  <AlertDescription>{error}</AlertDescription>
                </Alert>
              )}
            </div>

            <DialogFooter>
              <Button variant="outline" onClick={handleClose}>
                {t('common:buttons.cancel')}
              </Button>
              <Button onClick={handleGenerate}>
                <FileText className="h-4 w-4 mr-2" />
                {t('navigation:gsd.generatePlan')}
              </Button>
            </DialogFooter>
          </>
        ) : (
          <div className="space-y-4 py-4">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium">{t('navigation:gsd.generatingPlan')}</span>
              <Button variant="ghost" size="sm" onClick={handleCancel}>
                <X className="h-4 w-4" />
              </Button>
            </div>

            <Progress value={progress} />

            <ScrollArea className="h-[200px] rounded border p-3 bg-muted/30">
              <div ref={outputRef} className="space-y-1 font-mono text-xs">
                {output.map((line, i) => (
                  <div key={i} className="text-muted-foreground whitespace-pre-wrap">{line}</div>
                ))}
                {generating && (
                  <div className="flex items-center gap-2 text-primary">
                    <Loader2 className="h-3 w-3 animate-spin" />
                    <span>{t('navigation:gsd.processing')}</span>
                  </div>
                )}
              </div>
            </ScrollArea>

            {error && (
              <Alert variant="destructive">
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
