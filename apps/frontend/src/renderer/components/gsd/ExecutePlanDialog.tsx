import { useState, useEffect, useRef } from 'react';
import { useTranslation } from 'react-i18next';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '../ui/dialog';
import { Button } from '../ui/button';
import { Progress } from '../ui/progress';
import { ScrollArea } from '../ui/scroll-area';
import { Badge } from '../ui/badge';
import { Loader2, Play, X, CheckCircle2, XCircle } from 'lucide-react';
import { Alert, AlertDescription } from '../ui/alert';

interface ExecutePlanDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  projectPath: string;
  planPath: string;
  planName: string;
  onExecutionComplete: () => void;
}

export function ExecutePlanDialog({
  open,
  onOpenChange,
  projectPath,
  planPath,
  planName,
  onExecutionComplete
}: ExecutePlanDialogProps) {
  const { t } = useTranslation(['navigation', 'common']);
  const [executing, setExecuting] = useState(false);
  const [output, setOutput] = useState<string[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [progress, setProgress] = useState({ current: 0, total: 0 });
  const [generatorId, setGeneratorId] = useState<string | null>(null);
  const [completed, setCompleted] = useState<boolean | null>(null);
  const outputRef = useRef<HTMLDivElement>(null);
  const hasStarted = useRef(false);

  useEffect(() => {
    if (!executing || !generatorId) return;

    const unsubOutput = window.electronAPI.gsd.onExecuteOutput?.((data) => {
      if (data.generatorId === generatorId) {
        setOutput(prev => [...prev, data.data]);
      }
    });

    const unsubProgress = window.electronAPI.gsd.onExecuteProgress?.((data) => {
      if (data.generatorId === generatorId) {
        setProgress({ current: data.current, total: data.total });
      }
    });

    const unsubError = window.electronAPI.gsd.onExecuteError?.((data) => {
      if (data.generatorId === generatorId) {
        setError(data.error);
      }
    });

    const unsubComplete = window.electronAPI.gsd.onExecuteComplete?.((data) => {
      if (data.generatorId === generatorId) {
        setExecuting(false);
        setCompleted(data.success);
        if (data.success) {
          setTimeout(() => {
            onExecutionComplete();
          }, 1000);
        }
      }
    });

    return () => {
      unsubOutput?.();
      unsubProgress?.();
      unsubError?.();
      unsubComplete?.();
    };
  }, [executing, generatorId, onExecutionComplete]);

  useEffect(() => {
    if (outputRef.current) {
      outputRef.current.scrollTop = outputRef.current.scrollHeight;
    }
  }, [output]);

  // Auto-start on open
  useEffect(() => {
    if (open && !hasStarted.current && !executing && completed === null) {
      hasStarted.current = true;
      handleExecute();
    }
    if (!open) {
      hasStarted.current = false;
    }
  }, [open]);

  const handleExecute = async () => {
    setExecuting(true);
    setOutput([]);
    setError(null);
    setProgress({ current: 0, total: 0 });
    setCompleted(null);

    try {
      const result = await window.electronAPI.gsd.executePlan(projectPath, {
        planPath
      });

      if (result.success && result.data) {
        setGeneratorId(result.data.generatorId);
      } else {
        setError(result.error || t('navigation:gsd.executePlanFailed'));
        setExecuting(false);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : t('navigation:gsd.executePlanFailed'));
      setExecuting(false);
    }
  };

  const handleCancel = async () => {
    if (generatorId) {
      await window.electronAPI.gsd.cancelPlan(generatorId);
    }
    setExecuting(false);
    setGeneratorId(null);
  };

  const handleClose = () => {
    if (executing) {
      handleCancel();
    }
    setOutput([]);
    setError(null);
    setProgress({ current: 0, total: 0 });
    setCompleted(null);
    setGeneratorId(null);
    onOpenChange(false);
  };

  const progressPercent = progress.total > 0
    ? Math.round((progress.current / progress.total) * 100)
    : 0;

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-[700px]">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            {completed === true && <CheckCircle2 className="h-5 w-5 text-green-500" />}
            {completed === false && <XCircle className="h-5 w-5 text-red-500" />}
            {completed === null && <Play className="h-5 w-5" />}
            {t('navigation:gsd.executePlan')}
          </DialogTitle>
          <DialogDescription className="flex items-center gap-2">
            <span>{planName}</span>
            {executing && <Badge variant="secondary">{t('navigation:gsd.running')}</Badge>}
            {completed === true && <Badge variant="default" className="bg-green-500">{t('navigation:gsd.completed')}</Badge>}
            {completed === false && <Badge variant="destructive">{t('navigation:gsd.failed')}</Badge>}
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-4">
          {progress.total > 0 && (
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span>{t('navigation:gsd.tasks')}</span>
                <span>{progress.current}/{progress.total}</span>
              </div>
              <Progress value={progressPercent} />
            </div>
          )}

          <ScrollArea className="h-[300px] rounded border p-3 bg-muted/30">
            <div ref={outputRef} className="space-y-1 font-mono text-xs">
              {output.map((line, i) => (
                <div
                  key={i}
                  className={`whitespace-pre-wrap ${
                    line.includes('\u2713') || line.includes('\u2705') ? 'text-green-500' :
                    line.includes('\u2717') || line.includes('\u274c') ? 'text-red-500' :
                    line.includes('\ud83d\udd27') || line.includes('\ud83d\udcc1') ? 'text-blue-500' :
                    'text-muted-foreground'
                  }`}
                >
                  {line}
                </div>
              ))}
              {executing && (
                <div className="flex items-center gap-2 text-primary">
                  <Loader2 className="h-3 w-3 animate-spin" />
                  <span>{t('navigation:gsd.executing')}</span>
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

        <div className="flex justify-end gap-2">
          {executing ? (
            <Button variant="outline" onClick={handleCancel}>
              <X className="h-4 w-4 mr-2" />
              {t('common:buttons.cancel')}
            </Button>
          ) : (
            <Button variant="outline" onClick={handleClose}>
              {t('common:buttons.close')}
            </Button>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}
