'use client';

import { zodResolver } from '@hookform/resolvers/zod';
import { LoaderCircle, Pencil, Plus, RotateCcw } from 'lucide-react';
import { useCallback, useEffect, useRef, useState } from 'react';
import { useForm } from 'react-hook-form';
import { toast } from 'sonner';
import { z } from 'zod';

import {
  createTemplate,
  createTemplateVersion,
  getTemplate,
  listTemplateVersions,
  listTemplates,
  previewTemplate,
  rollbackTemplateVersion,
  updateTemplate,
} from '@/lib/api';
import type {
  PlaceholderInspectorResult,
  Template,
  TemplatePreviewResponse,
  TemplateSummary,
  TemplateVersion,
} from '@/lib/types';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Skeleton } from '@/components/ui/skeleton';

// ---------------------------------------------------------------------------
// Schemas
// ---------------------------------------------------------------------------

const createSchema = z.object({
  name: z.string().min(1, 'Name is required').max(120),
  description: z.string().optional(),
  subject_template: z.string().min(1, 'Subject template is required'),
  body_html_template: z.string().optional(),
  body_text_template: z.string().min(1, 'Plain-text body template is required'),
});

const editMetaSchema = z.object({
  name: z.string().min(1, 'Name is required').max(120),
  description: z.string().optional(),
});

const versionSchema = z.object({
  subject_template: z.string().min(1, 'Subject template is required'),
  body_html_template: z.string().optional(),
  body_text_template: z.string().min(1, 'Plain-text body template is required'),
});

type CreateForm = z.infer<typeof createSchema>;
type EditMetaForm = z.infer<typeof editMetaSchema>;
type VersionForm = z.infer<typeof versionSchema>;

// ---------------------------------------------------------------------------
// Helper sub-components
// ---------------------------------------------------------------------------

function FieldError({ message }: { message?: string }) {
  if (!message) return null;
  return <span className="text-xs text-rose-600 dark:text-rose-300">{message}</span>;
}

function InspectorPanel({ inspector }: { inspector: PlaceholderInspectorResult }) {
  return (
    <div className="rounded-xl border border-[var(--card-border)] bg-[var(--surface)] p-4 text-sm space-y-3">
      <p className="font-semibold text-[var(--foreground)]">Placeholder inspector</p>
      <div>
        <p className="text-xs text-[var(--muted)] mb-1">Used in template</p>
        {inspector.used_placeholders.length ? (
          <div className="flex flex-wrap gap-1">
            {inspector.used_placeholders.map((p) => (
              <Badge key={p}>{`{{${p}}}`}</Badge>
            ))}
          </div>
        ) : (
          <span className="text-[var(--muted)]">None</span>
        )}
      </div>
      {inspector.missing_placeholders.length > 0 && (
        <div>
          <p className="text-xs text-rose-500 mb-1 font-medium">Missing (required in template)</p>
          <div className="flex flex-wrap gap-1">
            {inspector.missing_placeholders.map((p) => (
              <Badge key={p} variant="destructive">{`{{${p}}}`}</Badge>
            ))}
          </div>
        </div>
      )}
      {inspector.unknown_payload_keys.length > 0 && (
        <div>
          <p className="text-xs text-amber-500 mb-1">Extra in payload (informational)</p>
          <div className="flex flex-wrap gap-1">
            {inspector.unknown_payload_keys.map((k) => (
              <Badge key={k} variant="warning">{k}</Badge>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Template list
// ---------------------------------------------------------------------------

function TemplateList({
  templates,
  loading,
  onSelect,
  onNew,
}: {
  templates: TemplateSummary[];
  loading: boolean;
  onSelect: (id: number) => void;
  onNew: () => void;
}) {
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">Templates</h2>
        <Button onClick={onNew} className="px-3 py-2 text-xs">
          <Plus className="size-4 mr-1" /> New template
        </Button>
      </div>
      {loading ? (
        <div className="space-y-2">
          {[...Array(3)].map((_, i) => (
            <Skeleton key={i} className="h-14 w-full rounded-xl" />
          ))}
        </div>
      ) : templates.length === 0 ? (
        <Card className="p-8 text-center text-[var(--muted)] text-sm">
          No templates yet — click &quot;New template&quot; to create one.
        </Card>
      ) : (
        <div className="space-y-2">
          {templates.map((t) => (
            <button
              key={t.id}
              onClick={() => onSelect(t.id)}
              className="w-full text-left rounded-xl border border-[var(--card-border)] bg-[var(--surface)] px-4 py-3 hover:bg-[var(--surface-hover,var(--surface))] transition-colors"
            >
              <p className="font-medium text-sm">{t.name}</p>
              {t.description && (
                <p className="text-xs text-[var(--muted)] mt-0.5 truncate">{t.description}</p>
              )}
              <p className="text-xs text-[var(--muted)] mt-1">
                Updated {new Date(t.updated_at).toLocaleDateString()}
              </p>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Create template form
// ---------------------------------------------------------------------------

function CreateTemplateForm({
  onCreated,
  onCancel,
}: {
  onCreated: (tmpl: Template) => void;
  onCancel: () => void;
}) {
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<CreateForm>({ resolver: zodResolver(createSchema) });

  const onSubmit = handleSubmit(async (values) => {
    try {
      const tmpl = await createTemplate({
        name: values.name,
        description: values.description ?? undefined,
        subject_template: values.subject_template,
        body_html_template: values.body_html_template ?? undefined,
        body_text_template: values.body_text_template,
      });
      toast.success('Template created');
      onCreated(tmpl);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Failed to create template');
    }
  });

  return (
    <Card className="p-6 space-y-4">
      <h3 className="font-semibold text-lg">New template</h3>
      <form onSubmit={onSubmit} className="space-y-4">
        <label className="block space-y-1 text-sm">
          <span className="font-medium">Name *</span>
          <Input {...register('name')} placeholder="Welcome Email" />
          <FieldError message={errors.name?.message} />
        </label>
        <label className="block space-y-1 text-sm">
          <span className="font-medium">Description</span>
          <Input {...register('description')} placeholder="Optional description" />
        </label>
        <label className="block space-y-1 text-sm">
          <span className="font-medium">Subject template *</span>
          <Input {...register('subject_template')} placeholder="Hello {{first_name}}!" />
          <FieldError message={errors.subject_template?.message} />
        </label>
        <label className="block space-y-1 text-sm">
          <span className="font-medium">Plain-text body *</span>
          <textarea
            {...register('body_text_template')}
            rows={4}
            className="w-full rounded-2xl border border-[var(--card-border)] bg-[var(--surface)] px-4 py-3 text-sm outline-none font-mono"
            placeholder="Hi {{first_name}}, welcome to {{company}}!"
          />
          <FieldError message={errors.body_text_template?.message} />
        </label>
        <label className="block space-y-1 text-sm">
          <span className="font-medium">HTML body (optional)</span>
          <textarea
            {...register('body_html_template')}
            rows={4}
            className="w-full rounded-2xl border border-[var(--card-border)] bg-[var(--surface)] px-4 py-3 text-sm outline-none font-mono"
            placeholder="<p>Hi <strong>{{first_name}}</strong>, welcome!</p>"
          />
        </label>
        <div className="flex gap-2">
          <Button type="submit" disabled={isSubmitting}>
            {isSubmitting && <LoaderCircle className="size-4 animate-spin mr-1" />}
            Create
          </Button>
          <Button type="button" variant="outline" onClick={onCancel}>Cancel</Button>
        </div>
      </form>
    </Card>
  );
}

// ---------------------------------------------------------------------------
// Template editor (detail view with preview + versioning)
// ---------------------------------------------------------------------------

function TemplateEditor({ templateId, onBack }: { templateId: number; onBack: () => void }) {
  const [template, setTemplate] = useState<Template | null>(null);
  const [versions, setVersions] = useState<TemplateVersion[]>([]);
  const [loading, setLoading] = useState(true);
  const [preview, setPreview] = useState<TemplatePreviewResponse | null>(null);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [samplePayload, setSamplePayload] = useState('{}');
  const [payloadError, setPayloadError] = useState<string | null>(null);
  const [showHtml, setShowHtml] = useState(false);
  const [editingMeta, setEditingMeta] = useState(false);
  const previewTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  const {
    register: vReg,
    handleSubmit: vSubmit,
    reset: vReset,
    formState: { errors: vErrors, isSubmitting: vSubmitting },
  } = useForm<VersionForm>({ resolver: zodResolver(versionSchema) });

  const {
    register: mReg,
    handleSubmit: mSubmit,
    reset: mReset,
    formState: { errors: mErrors, isSubmitting: mSubmitting },
  } = useForm<EditMetaForm>({ resolver: zodResolver(editMetaSchema) });

  const reload = useCallback(async () => {
    const [tmpl, vers] = await Promise.all([
      getTemplate(templateId),
      listTemplateVersions(templateId),
    ]);
    setTemplate(tmpl);
    setVersions(vers);
    if (tmpl.current_version) {
      vReset({
        subject_template: tmpl.current_version.subject_template,
        body_html_template: tmpl.current_version.body_html_template ?? '',
        body_text_template: tmpl.current_version.body_text_template,
      });
    }
    mReset({ name: tmpl.name, description: tmpl.description ?? '' });
  }, [templateId, vReset, mReset]);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      reload().finally(() => setLoading(false));
    }, 0);
    return () => window.clearTimeout(timer);
  }, [reload]);

  const runPreview = useCallback(
    async (payload: string) => {
      let variables: Record<string, string> = {};
      try {
        variables = JSON.parse(payload) as Record<string, string>;
        setPayloadError(null);
      } catch {
        setPayloadError('Invalid JSON');
        return;
      }
      setPreviewLoading(true);
      try {
        const result = await previewTemplate(templateId, { variables });
        setPreview(result);
      } catch {
        // swallow preview errors silently
      } finally {
        setPreviewLoading(false);
      }
    },
    [templateId],
  );

  const handlePayloadChange = (val: string) => {
    setSamplePayload(val);
    if (previewTimer.current) clearTimeout(previewTimer.current);
    previewTimer.current = setTimeout(() => { void runPreview(val); }, 500);
  };

  const onSaveVersion = vSubmit(async (values) => {
    try {
      await createTemplateVersion(templateId, {
        subject_template: values.subject_template,
        body_html_template: values.body_html_template ?? undefined,
        body_text_template: values.body_text_template,
      });
      toast.success('New version saved');
      await reload();
      await runPreview(samplePayload);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Failed to save version');
    }
  });

  const onSaveMeta = mSubmit(async (values) => {
    try {
      await updateTemplate(templateId, {
        name: values.name,
        description: values.description ?? undefined,
      });
      toast.success('Metadata updated');
      setEditingMeta(false);
      await reload();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Failed to update metadata');
    }
  });

  const onRollback = async (versionId: number) => {
    try {
      await rollbackTemplateVersion(templateId, versionId);
      toast.success('Rolled back to version');
      await reload();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Rollback failed');
    }
  };

  if (loading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-8 w-48" />
        <Skeleton className="h-64 w-full" />
      </div>
    );
  }

  if (!template) return null;

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <button onClick={onBack} className="text-sm text-[var(--muted)] hover:underline">← Back</button>
        {editingMeta ? (
          <form onSubmit={onSaveMeta} className="flex items-center gap-2">
            <Input {...mReg('name')} className="h-8 text-base font-semibold" />
            <Button type="submit" disabled={mSubmitting} className="px-3 py-1.5 text-xs">Save</Button>
            <Button type="button" variant="outline" onClick={() => setEditingMeta(false)} className="px-3 py-1.5 text-xs">Cancel</Button>
            <FieldError message={mErrors.name?.message} />
          </form>
        ) : (
          <div className="flex items-center gap-2">
            <h2 className="text-lg font-semibold">{template.name}</h2>
            <button onClick={() => setEditingMeta(true)} className="text-[var(--muted)] hover:text-[var(--foreground)]">
              <Pencil className="size-3.5" />
            </button>
          </div>
        )}
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Left: editor */}
        <div className="space-y-4">
          <Card className="p-5 space-y-4">
            <p className="font-semibold text-sm">Edit template content</p>
            <label className="block space-y-1 text-sm">
              <span className="font-medium">Subject</span>
              <Input {...vReg('subject_template')} />
              <FieldError message={vErrors.subject_template?.message} />
            </label>
            <label className="block space-y-1 text-sm">
              <span className="font-medium">Plain-text body</span>
              <textarea
                {...vReg('body_text_template')}
                rows={6}
                className="w-full rounded-2xl border border-[var(--card-border)] bg-[var(--surface)] px-4 py-3 text-sm outline-none font-mono"
              />
              <FieldError message={vErrors.body_text_template?.message} />
            </label>
            <label className="block space-y-1 text-sm">
              <span className="font-medium">HTML body (optional)</span>
              <textarea
                {...vReg('body_html_template')}
                rows={6}
                className="w-full rounded-2xl border border-[var(--card-border)] bg-[var(--surface)] px-4 py-3 text-sm outline-none font-mono"
              />
            </label>
            <Button onClick={onSaveVersion} disabled={vSubmitting}>
              {vSubmitting && <LoaderCircle className="size-4 animate-spin mr-1" />}
              Save as new version
            </Button>
          </Card>

          {/* Sample payload */}
          <Card className="p-5 space-y-3">
            <p className="font-semibold text-sm">Sample payload (JSON)</p>
            <textarea
              value={samplePayload}
              onChange={(e) => handlePayloadChange(e.target.value)}
              rows={4}
              className="w-full rounded-2xl border border-[var(--card-border)] bg-[var(--surface)] px-4 py-3 text-sm outline-none font-mono"
              placeholder='{"first_name": "Alice", "company": "Acme"}'
            />
            {payloadError && <p className="text-xs text-rose-500">{payloadError}</p>}
            <Button variant="outline" onClick={() => { void runPreview(samplePayload); }} disabled={previewLoading} className="px-3 py-1.5 text-xs">
              {previewLoading && <LoaderCircle className="size-3.5 animate-spin mr-1" />}
              Refresh preview
            </Button>
          </Card>
        </div>

        {/* Right: preview + inspector */}
        <div className="space-y-4">
          <Card className="p-5 space-y-3">
            <div className="flex items-center justify-between">
              <p className="font-semibold text-sm">Preview</p>
              <button
                className="text-xs text-[var(--muted)] hover:underline"
                onClick={() => setShowHtml((v) => !v)}
              >
                {showHtml ? 'Show rendered' : 'Show HTML source'}
              </button>
            </div>
            {preview ? (
              <div className="space-y-3">
                <div>
                  <p className="text-xs text-[var(--muted)] mb-0.5">Subject</p>
                  <p className="text-sm font-medium">{preview.subject}</p>
                </div>
                {preview.html_safety_warnings.length > 0 && (
                  <div className="rounded-lg bg-amber-50 dark:bg-amber-900/20 border border-amber-300 px-3 py-2 text-xs text-amber-700 dark:text-amber-300 space-y-1">
                    {preview.html_safety_warnings.map((w, i) => (
                      <p key={i}>⚠️ {w}</p>
                    ))}
                  </div>
                )}
                {showHtml ? (
                  <pre className="rounded-xl border border-[var(--card-border)] bg-[var(--surface)] p-3 text-xs overflow-auto max-h-64">
                    {preview.body_html ?? '(no HTML body)'}
                  </pre>
                ) : preview.body_html ? (
                  <iframe
                    srcDoc={preview.body_html}
                    sandbox=""
                    className="w-full h-48 rounded-xl border border-[var(--card-border)]"
                    title="Email preview"
                  />
                ) : (
                  <pre className="rounded-xl border border-[var(--card-border)] bg-[var(--surface)] p-3 text-xs overflow-auto max-h-48 whitespace-pre-wrap">
                    {preview.body_text}
                  </pre>
                )}
              </div>
            ) : (
              <p className="text-sm text-[var(--muted)]">Enter a sample payload and click &quot;Refresh preview&quot;.</p>
            )}
          </Card>

          {preview && <InspectorPanel inspector={preview.inspector} />}

          {/* Version history */}
          <Card className="p-5 space-y-3">
            <p className="font-semibold text-sm">Version history</p>
            {versions.length === 0 ? (
              <p className="text-sm text-[var(--muted)]">No versions yet.</p>
            ) : (
              <div className="space-y-2">
                {[...versions].reverse().map((v) => (
                  <div
                    key={v.id}
                    className="flex items-center justify-between rounded-lg border border-[var(--card-border)] px-3 py-2 text-sm"
                  >
                    <div>
                      <span className="font-medium">v{v.version_number}</span>
                      {template.current_version_id === v.id && (
                        <Badge className="ml-2 text-xs">current</Badge>
                      )}
                      <p className="text-xs text-[var(--muted)]">
                        {new Date(v.created_at).toLocaleString()}
                      </p>
                    </div>
                    {template.current_version_id !== v.id && (
                      <button
                        onClick={() => { void onRollback(v.id); }}
                        className="flex items-center gap-1 text-xs text-[var(--muted)] hover:text-[var(--foreground)]"
                      >
                        <RotateCcw className="size-3" /> rollback
                      </button>
                    )}
                  </div>
                ))}
              </div>
            )}
          </Card>
        </div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main view
// ---------------------------------------------------------------------------

type View = { type: 'list' } | { type: 'new' } | { type: 'edit'; id: number };

export function TemplatesView() {
  const [view, setView] = useState<View>({ type: 'list' });
  const [templates, setTemplates] = useState<TemplateSummary[]>([]);
  const [loadingList, setLoadingList] = useState(true);

  const refreshList = useCallback(async () => {
    setLoadingList(true);
    try {
      setTemplates(await listTemplates());
    } finally {
      setLoadingList(false);
    }
  }, []);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      void refreshList();
    }, 0);
    return () => window.clearTimeout(timer);
  }, [refreshList]);

  if (view.type === 'edit') {
    return (
      <TemplateEditor
        templateId={view.id}
        onBack={() => {
          setView({ type: 'list' });
          void refreshList();
        }}
      />
    );
  }

  if (view.type === 'new') {
    return (
      <CreateTemplateForm
        onCreated={(tmpl) => {
          setView({ type: 'edit', id: tmpl.id });
          void refreshList();
        }}
        onCancel={() => setView({ type: 'list' })}
      />
    );
  }

  return (
    <TemplateList
      templates={templates}
      loading={loadingList}
      onSelect={(id) => setView({ type: 'edit', id })}
      onNew={() => setView({ type: 'new' })}
    />
  );
}
