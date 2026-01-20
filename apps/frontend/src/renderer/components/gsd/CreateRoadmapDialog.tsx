/**
 * CreateRoadmapDialog - Dialog for AI-powered roadmap generation
 *
 * Allows users to input project goals and select depth,
 * then streams Claude CLI output in real-time.
 */

import { useState, useEffect, useRef, useCallback } from 'react';
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
import { RadioGroup, RadioGroupItem } from '../ui/radio-group';
import { Progress } from '../ui/progress';
import { ScrollArea } from '../ui/scroll-area';
import { Loader2, Sparkles, X } from 'lucide-react';
import { Alert, AlertDescription } from '../ui/alert';

type Depth = 'quick' | 'standard' | 'comprehensive';

interface CreateRoadmapDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  projectPath: string;
  onRoadmapCreated: () => void;
}

export function CreateRoadmapDialog({
  open,
  onOpenChange,
  projectPath,
  onRoadmapCreated
}: CreateRoadmapDialogProps) {
  const { t } = useTranslation(['navigation', 'common']);
  const [goals, setGoals] = useState('');
  const [depth, setDepth] = useState<Depth>('standard');
  const [generating, setGenerating] = useState(false);
  const [output, setOutput] = useState<string[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [progress, setProgress] = useState(0);
  const [generatorId, setGeneratorId] = useState<string | null>(null);
  const outputRef = useRef<HTMLDivElement>(null);

  // Setup event listeners
  useEffect(() => {
    if (!generating || !generatorId) return;

    const unsubOutput = window.electronAPI.gsd.onRoadmapOutput?.((data) => {
      if (data.generatorId === generatorId) {
        setOutput(prev => [...prev, data.data]);
        setProgress(prev => Math.min(prev + 5, 90));
      }
    });

    const unsubError = window.electronAPI.gsd.onRoadmapError?.((data) => {
      if (data.generatorId === generatorId) {
        setError(data.error);
      }
    });

    const unsubComplete = window.electronAPI.gsd.onRoadmapComplete?.((data) => {
      if (data.generatorId === generatorId) {
        setGenerating(false);
        setProgress(100);
        if (data.success) {
          setTimeout(() => {
            onRoadmapCreated();
            handleClose();
          }, 500);
        }
      }
    });

    return () => {
      unsubOutput?.();
      unsubError?.();
      unsubComplete?.();
    };
  }, [generating, generatorId, onRoadmapCreated]);

  // Auto-scroll output
  useEffect(() => {
    if (outputRef.current) {
      outputRef.current.scrollTop = outputRef.current.scrollHeight;
    }
  }, [output]);

  const handleGenerate = useCallback(async () => {
    if (!goals.trim()) {
      setError(t('navigation:gsd.goalsRequired'));
      return;
    }

    setGenerating(true);
    setOutput([]);
    setError(null);
    setProgress(0);

    try {
      const result = await window.electronAPI.gsd.generateRoadmap(projectPath, {
        goals: goals.trim(),
        depth
      });

      if (result.success && result.data) {
        setGeneratorId(result.data.generatorId);
      } else {
        setError(result.error || t('navigation:gsd.generateFailed'));
        setGenerating(false);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : t('navigation:gsd.generateFailed'));
      setGenerating(false);
    }
  }, [goals, depth, projectPath, t]);

  const handleCancel = useCallback(async () => {
    if (generatorId) {
      await window.electronAPI.gsd.cancelGeneration(generatorId);
    }
    setGenerating(false);
    setGeneratorId(null);
  }, [generatorId]);

  const handleClose = useCallback(() => {
    if (generating) {
      handleCancel();
    }
    setGoals('');
    setDepth('standard');
    setOutput([]);
    setError(null);
    setProgress(0);
    onOpenChange(false);
  }, [generating, handleCancel, onOpenChange]);

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-[600px]">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Sparkles className="h-5 w-5" />
            {t('navigation:gsd.createRoadmap')}
          </DialogTitle>
          <DialogDescription>
            {t('navigation:gsd.createRoadmapDescription')}
          </DialogDescription>
        </DialogHeader>

        {!generating ? (
          <>
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label htmlFor="goals">{t('navigation:gsd.whatToBuild')}</Label>
                <Textarea
                  id="goals"
                  value={goals}
                  onChange={(e) => setGoals(e.target.value)}
                  placeholder={t('navigation:gsd.goalsPlaceholder')}
                  rows={5}
                />
              </div>

              <div className="space-y-2">
                <Label>{t('navigation:gsd.depth')}</Label>
                <RadioGroup value={depth} onValueChange={(v) => setDepth(v as Depth)}>
                  <div className="flex items-center space-x-2">
                    <RadioGroupItem value="quick" id="quick" />
                    <Label htmlFor="quick" className="font-normal">
                      {t('navigation:gsd.depthQuick')} (3-5 phases)
                    </Label>
                  </div>
                  <div className="flex items-center space-x-2">
                    <RadioGroupItem value="standard" id="standard" />
                    <Label htmlFor="standard" className="font-normal">
                      {t('navigation:gsd.depthStandard')} (5-8 phases)
                    </Label>
                  </div>
                  <div className="flex items-center space-x-2">
                    <RadioGroupItem value="comprehensive" id="comprehensive" />
                    <Label htmlFor="comprehensive" className="font-normal">
                      {t('navigation:gsd.depthComprehensive')} (8-12 phases)
                    </Label>
                  </div>
                </RadioGroup>
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
                <Sparkles className="h-4 w-4 mr-2" />
                {t('navigation:gsd.generateRoadmap')}
              </Button>
            </DialogFooter>
          </>
        ) : (
          <div className="space-y-4 py-4">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium">{t('navigation:gsd.generatingRoadmap')}</span>
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
