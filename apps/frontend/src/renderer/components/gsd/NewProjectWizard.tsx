import { useState } from 'react';
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
import { Input } from '../ui/input';
import { Textarea } from '../ui/textarea';
import { Label } from '../ui/label';
import { Loader2, FolderPlus } from 'lucide-react';
import { Alert, AlertDescription } from '../ui/alert';

interface NewProjectWizardProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  projectPath: string;
  onProjectCreated: () => void;
}

export function NewProjectWizard({
  open,
  onOpenChange,
  projectPath,
  onProjectCreated
}: NewProjectWizardProps) {
  const { t } = useTranslation(['navigation', 'common']);
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [coreValue, setCoreValue] = useState('');
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleCreate = async () => {
    if (!name.trim()) {
      setError(t('navigation:gsd.projectNameRequired'));
      return;
    }
    if (!description.trim()) {
      setError(t('navigation:gsd.projectDescriptionRequired'));
      return;
    }

    setCreating(true);
    setError(null);

    try {
      const result = await window.electronAPI.gsd.createProject(projectPath, {
        name: name.trim(),
        description: description.trim(),
        coreValue: coreValue.trim() || undefined
      });

      if (result.success) {
        onProjectCreated();
        onOpenChange(false);
        // Reset form
        setName('');
        setDescription('');
        setCoreValue('');
      } else {
        setError(result.error || t('navigation:gsd.createProjectFailed'));
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : t('navigation:gsd.createProjectFailed'));
    } finally {
      setCreating(false);
    }
  };

  const handleClose = (isOpen: boolean) => {
    if (!creating) {
      onOpenChange(isOpen);
      // Reset form when closing
      if (!isOpen) {
        setError(null);
      }
    }
  };

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <FolderPlus className="h-5 w-5" />
            {t('navigation:gsd.newProject')}
          </DialogTitle>
          <DialogDescription>
            {t('navigation:gsd.newProjectDescription')}
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-4">
          <div className="space-y-2">
            <Label htmlFor="project-name">{t('navigation:gsd.projectName')} *</Label>
            <Input
              id="project-name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder={t('navigation:gsd.projectNamePlaceholder')}
              disabled={creating}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="project-description">{t('navigation:gsd.projectDescription')} *</Label>
            <Textarea
              id="project-description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder={t('navigation:gsd.projectDescriptionPlaceholder')}
              rows={3}
              disabled={creating}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="core-value">{t('navigation:gsd.coreValue')}</Label>
            <Input
              id="core-value"
              value={coreValue}
              onChange={(e) => setCoreValue(e.target.value)}
              placeholder={t('navigation:gsd.coreValuePlaceholder')}
              disabled={creating}
            />
            <p className="text-xs text-muted-foreground">
              {t('navigation:gsd.coreValueHint')}
            </p>
          </div>

          {error && (
            <Alert variant="destructive">
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => handleClose(false)} disabled={creating}>
            {t('common:buttons.cancel')}
          </Button>
          <Button onClick={handleCreate} disabled={creating}>
            {creating ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                {t('common:labels.creating')}
              </>
            ) : (
              <>
                <FolderPlus className="h-4 w-4 mr-2" />
                {t('navigation:gsd.createProject')}
              </>
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
