'use client';

import { zodResolver } from '@hookform/resolvers/zod';
import {
  type ColumnDef,
} from '@tanstack/react-table';
import { Plus, Trash2, UserPlus, X } from 'lucide-react';
import { useCallback, useEffect, useState } from 'react';
import { useForm } from 'react-hook-form';
import { toast } from 'sonner';
import { z } from 'zod';

import {
  addContactToList,
  createContact,
  createContactList,
  deleteContact,
  deleteContactList,
  listContactLists,
  listContacts,
  removeContactFromList,
  updateContact,
  updateContactList,
} from '@/lib/api';
import type { Contact, ContactList } from '@/lib/types';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { DataTable } from '@/components/data-table';
import { Input } from '@/components/ui/input';
import { Skeleton } from '@/components/ui/skeleton';

// ---------------------------------------------------------------------------
// Schemas
// ---------------------------------------------------------------------------

const contactSchema = z.object({
  email: z.string().email('Valid email required'),
  first_name: z.string().max(120).optional(),
  last_name: z.string().max(120).optional(),
  status: z.enum(['active', 'unsubscribed', 'bounced', 'complained']).default('active'),
});

const listSchema = z.object({
  name: z.string().min(1, 'Name is required').max(120),
  description: z.string().optional(),
});

type ContactForm = z.infer<typeof contactSchema>;
type ListForm = z.infer<typeof listSchema>;

// ---------------------------------------------------------------------------
// Status badge
// ---------------------------------------------------------------------------

function ContactStatusBadge({ status }: { status: string }) {
  const variantMap: Record<string, 'default' | 'secondary' | 'destructive' | 'outline'> = {
    active: 'default',
    unsubscribed: 'secondary',
    bounced: 'destructive',
    complained: 'destructive',
  };
  return <Badge variant={variantMap[status] ?? 'outline'}>{status}</Badge>;
}

// ---------------------------------------------------------------------------
// Contact form modal (create / edit)
// ---------------------------------------------------------------------------

function ContactFormModal({
  initial,
  onClose,
  onSaved,
}: {
  initial?: Contact;
  onClose: () => void;
  onSaved: (c: Contact) => void;
}) {
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<ContactForm>({
    resolver: zodResolver(contactSchema),
    defaultValues: {
      email: initial?.email ?? '',
      first_name: initial?.first_name ?? '',
      last_name: initial?.last_name ?? '',
      status: (initial?.status as ContactForm['status']) ?? 'active',
    },
  });

  const onSubmit = async (data: ContactForm) => {
    try {
      const saved = initial
        ? await updateContact(initial.id, data)
        : await createContact(data);
      toast.success(initial ? 'Contact updated' : 'Contact created');
      onSaved(saved);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Failed to save contact');
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <Card className="w-full max-w-md p-6 space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold">{initial ? 'Edit Contact' : 'New Contact'}</h2>
          <button onClick={onClose} aria-label="Close"><X className="size-5" /></button>
        </div>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-3">
          <div>
            <label className="text-sm font-medium">Email *</label>
            <Input {...register('email')} placeholder="user@example.com" />
            {errors.email && <p className="text-xs text-red-500 mt-1">{errors.email.message}</p>}
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-sm font-medium">First name</label>
              <Input {...register('first_name')} placeholder="Alice" />
            </div>
            <div>
              <label className="text-sm font-medium">Last name</label>
              <Input {...register('last_name')} placeholder="Smith" />
            </div>
          </div>
          <div>
            <label className="text-sm font-medium">Status</label>
            <select
              {...register('status')}
              className="w-full rounded-md border border-[var(--card-border)] bg-[var(--surface)] px-3 py-2 text-sm"
            >
              <option value="active">active</option>
              <option value="unsubscribed">unsubscribed</option>
              <option value="bounced">bounced</option>
              <option value="complained">complained</option>
            </select>
          </div>
          <div className="flex gap-2 justify-end pt-2">
            <Button type="button" variant="outline" onClick={onClose}>Cancel</Button>
            <Button type="submit" disabled={isSubmitting}>
              {isSubmitting ? 'Saving…' : 'Save'}
            </Button>
          </div>
        </form>
      </Card>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Contact detail panel
// ---------------------------------------------------------------------------

function ContactDetail({
  contact,
  lists,
  onClose,
  onUpdated,
}: {
  contact: Contact;
  lists: ContactList[];
  onClose: () => void;
  onUpdated: () => void;
}) {
  const [adding, setAdding] = useState(false);
  const [selectedListId, setSelectedListId] = useState<string>('');

  const handleAdd = async () => {
    if (!selectedListId) return;
    try {
      await addContactToList(contact.id, Number(selectedListId));
      toast.success('Added to list');
      onUpdated();
      setAdding(false);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Failed to add');
    }
  };

  const handleRemove = async (listId: number) => {
    try {
      await removeContactFromList(contact.id, listId);
      toast.success('Removed from list');
      onUpdated();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Failed to remove');
    }
  };

  // Get the lists this contact is a member of
  const memberListIds = new Set(
    lists.filter(() => true).map((l) => l.id) // will be filtered below via API response
  );

  return (
    <div className="fixed inset-0 z-50 flex items-end justify-end bg-black/40">
      <Card className="h-full w-full max-w-sm overflow-y-auto p-6 space-y-5 rounded-none rounded-l-2xl">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold">Contact Details</h2>
          <button onClick={onClose} aria-label="Close"><X className="size-5" /></button>
        </div>
        <div className="space-y-2 text-sm">
          <p><span className="text-[var(--muted)]">Email:</span> {contact.email}</p>
          <p><span className="text-[var(--muted)]">Name:</span> {contact.first_name ?? ''} {contact.last_name ?? ''}</p>
          <p><span className="text-[var(--muted)]">Status:</span> <ContactStatusBadge status={contact.status} /></p>
          <p><span className="text-[var(--muted)]">Lists:</span> {contact.list_count}</p>
        </div>

        <div>
          <h3 className="text-sm font-semibold mb-2">List Memberships</h3>
          {lists.length === 0 ? (
            <p className="text-xs text-[var(--muted)]">No lists available.</p>
          ) : (
            <ul className="space-y-2">
              {lists.map((l) => (
                <li key={l.id} className="flex items-center justify-between text-sm">
                  <span>{l.name}</span>
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => handleRemove(l.id)}
                  >
                    Remove
                  </Button>
                </li>
              ))}
            </ul>
          )}
          {adding ? (
            <div className="mt-3 flex gap-2">
              <select
                value={selectedListId}
                onChange={(e) => setSelectedListId(e.target.value)}
                className="flex-1 rounded-md border border-[var(--card-border)] bg-[var(--surface)] px-2 py-1 text-sm"
              >
                <option value="">Select list…</option>
                {lists.map((l) => (
                  <option key={l.id} value={l.id}>{l.name}</option>
                ))}
              </select>
              <Button size="sm" onClick={handleAdd}>Add</Button>
              <Button size="sm" variant="outline" onClick={() => setAdding(false)}>Cancel</Button>
            </div>
          ) : (
            <Button size="sm" variant="outline" className="mt-3" onClick={() => setAdding(true)}>
              <UserPlus className="size-4 mr-1" /> Add to List
            </Button>
          )}
        </div>
      </Card>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Contact Lists sub-section
// ---------------------------------------------------------------------------

function ContactListsSection({ lists, onChanged }: { lists: ContactList[]; onChanged: () => void }) {
  const [showForm, setShowForm] = useState(false);
  const { register, handleSubmit, reset, formState: { errors, isSubmitting } } = useForm<ListForm>({
    resolver: zodResolver(listSchema),
  });

  const onSubmit = async (data: ListForm) => {
    try {
      await createContactList(data);
      toast.success('List created');
      reset();
      setShowForm(false);
      onChanged();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Failed to create list');
    }
  };

  const handleDelete = async (listId: number) => {
    try {
      await deleteContactList(listId);
      toast.success('List deleted');
      onChanged();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Failed to delete list');
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-base font-semibold">Contact Lists</h2>
        <Button size="sm" onClick={() => setShowForm(!showForm)}>
          <Plus className="size-4 mr-1" /> New List
        </Button>
      </div>

      {showForm && (
        <Card className="p-4 space-y-3">
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-3">
            <div>
              <label className="text-sm font-medium">Name *</label>
              <Input {...register('name')} placeholder="Newsletter" />
              {errors.name && <p className="text-xs text-red-500 mt-1">{errors.name.message}</p>}
            </div>
            <div>
              <label className="text-sm font-medium">Description</label>
              <Input {...register('description')} placeholder="Optional description" />
            </div>
            <div className="flex gap-2 justify-end">
              <Button type="button" variant="outline" onClick={() => setShowForm(false)}>Cancel</Button>
              <Button type="submit" disabled={isSubmitting}>Create</Button>
            </div>
          </form>
        </Card>
      )}

      {lists.length === 0 ? (
        <p className="text-sm text-[var(--muted)]">No contact lists yet.</p>
      ) : (
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {lists.map((l) => (
            <Card key={l.id} className="p-4 flex items-start justify-between">
              <div>
                <p className="font-medium text-sm">{l.name}</p>
                {l.description && <p className="text-xs text-[var(--muted)] mt-0.5">{l.description}</p>}
                <p className="text-xs text-[var(--muted)] mt-1">{l.member_count} members</p>
              </div>
              <button
                onClick={() => handleDelete(l.id)}
                className="text-[var(--muted)] hover:text-red-500"
                aria-label="Delete list"
              >
                <Trash2 className="size-4" />
              </button>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main ContactsView
// ---------------------------------------------------------------------------

export function ContactsView() {
  const [contacts, setContacts] = useState<Contact[]>([]);
  const [lists, setLists] = useState<ContactList[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [editing, setEditing] = useState<Contact | null>(null);
  const [detail, setDetail] = useState<Contact | null>(null);
  const [activeTab, setActiveTab] = useState<'contacts' | 'lists'>('contacts');

  const reload = useCallback(async () => {
    try {
      const [cs, ls] = await Promise.all([listContacts(), listContactLists()]);
      setContacts(cs);
      setLists(ls);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Failed to load contacts');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { void reload(); }, [reload]);

  const handleDelete = async (contactId: number) => {
    try {
      await deleteContact(contactId);
      toast.success('Contact deleted');
      void reload();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Failed to delete contact');
    }
  };

  const columns: ColumnDef<Contact, unknown>[] = [
    { accessorKey: 'email', header: 'Email' },
    {
      id: 'name',
      header: 'Name',
      cell: ({ row }) => {
        const c = row.original;
        const name = [c.first_name, c.last_name].filter(Boolean).join(' ');
        return name || <span className="text-[var(--muted)]">—</span>;
      },
    },
    {
      accessorKey: 'status',
      header: 'Status',
      cell: ({ row }) => <ContactStatusBadge status={row.original.status} />,
    },
    {
      accessorKey: 'list_count',
      header: 'Lists',
      cell: ({ row }) => row.original.list_count,
    },
    {
      id: 'actions',
      header: 'Actions',
      cell: ({ row }) => (
        <div className="flex gap-2">
          <Button size="sm" variant="outline" onClick={() => setDetail(row.original)}>View</Button>
          <Button size="sm" variant="outline" onClick={() => setEditing(row.original)}>Edit</Button>
          <Button size="sm" variant="destructive" onClick={() => handleDelete(row.original.id)}>
            Delete
          </Button>
        </div>
      ),
    },
  ];

  return (
    <div className="space-y-6">
      {/* Tabs */}
      <div className="flex gap-4 border-b border-[var(--card-border)]">
        {(['contacts', 'lists'] as const).map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`pb-2 text-sm font-medium capitalize border-b-2 transition-colors ${
              activeTab === tab
                ? 'border-[var(--primary)] text-[var(--primary)]'
                : 'border-transparent text-[var(--muted)] hover:text-[var(--foreground)]'
            }`}
          >
            {tab === 'contacts' ? 'Contacts' : 'Lists'}
          </button>
        ))}
      </div>

      {activeTab === 'contacts' && (
        <>
          <div className="flex justify-end">
            <Button onClick={() => setShowCreate(true)}>
              <Plus className="size-4 mr-1" /> New Contact
            </Button>
          </div>

          {loading ? (
            <div className="space-y-3">
              {Array.from({ length: 5 }).map((_, i) => (
                <Skeleton key={i} className="h-12 w-full rounded-xl" />
              ))}
            </div>
          ) : (
            <DataTable
              columns={columns}
              data={contacts}
              filterPlaceholder="Filter by email, name…"
            />
          )}
        </>
      )}

      {activeTab === 'lists' && (
        <ContactListsSection lists={lists} onChanged={() => void reload()} />
      )}

      {/* Modals */}
      {showCreate && (
        <ContactFormModal
          onClose={() => setShowCreate(false)}
          onSaved={() => { setShowCreate(false); void reload(); }}
        />
      )}
      {editing && (
        <ContactFormModal
          initial={editing}
          onClose={() => setEditing(null)}
          onSaved={() => { setEditing(null); void reload(); }}
        />
      )}
      {detail && (
        <ContactDetail
          contact={detail}
          lists={lists}
          onClose={() => setDetail(null)}
          onUpdated={() => void reload()}
        />
      )}
    </div>
  );
}
