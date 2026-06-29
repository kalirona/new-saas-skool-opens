'use client'
import React, { useState } from 'react'
import { useTranslation } from 'react-i18next'
import toast from 'react-hot-toast'
import { useLHSession } from '@components/Contexts/LHSessionContext'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { getSpaces, createSpace, updateSpace, deleteSpace, Space, SpaceCreate } from '@services/communities/spaces'
import { getAPIUrl } from '@services/config/config'
import Modal from '@components/Objects/StyledElements/Modal/Modal'
import { Plus, Trash2, GripVertical, Pencil, Loader2, AlertCircle } from 'lucide-react'
import { DragDropContext, Droppable, Draggable } from '@hello-pangea/dnd'

interface ManageSpacesModalProps {
  isOpen: boolean
  onClose: () => void
  communityUuid: string
}

const VISIBILITY_OPTIONS = [
  { value: 'public', label: 'Public' },
  { value: 'members', label: 'Members' },
  { value: 'moderators', label: 'Moderators' },
]

export function ManageSpacesModal({
  isOpen,
  onClose,
  communityUuid,
}: ManageSpacesModalProps) {
  const { t } = useTranslation()
  const session = useLHSession() as any
  const accessToken = session?.data?.tokens?.access_token
  const queryClient = useQueryClient()
  const [isCreateOpen, setIsCreateOpen] = useState(false)
  const [editingSpace, setEditingSpace] = useState<Space | null>(null)
  const [name, setName] = useState('')
  const [icon, setIcon] = useState('')
  const [description, setDescription] = useState('')
  const [visibility, setVisibility] = useState('public')
  const [isSaving, setIsSaving] = useState(false)
  const [deleteConfirm, setDeleteConfirm] = useState<string | null>(null)

  const { data: spaces = [], isLoading } = useQuery<Space[]>({
    queryKey: ['community', communityUuid, 'spaces'],
    queryFn: () => getSpaces(communityUuid, accessToken),
    enabled: !!communityUuid && !!accessToken,
    staleTime: 0,
  })

  const refreshSpaces = () => {
    queryClient.invalidateQueries({ queryKey: ['community', communityUuid, 'spaces'] })
  }

  const resetForm = () => {
    setName('')
    setIcon('')
    setDescription('')
    setVisibility('public')
    setEditingSpace(null)
    setIsCreateOpen(false)
  }

  const handleSave = async () => {
    if (!name.trim() || !accessToken) return
    setIsSaving(true)
    try {
      if (editingSpace) {
        await updateSpace(editingSpace.space_uuid, { name: name.trim(), icon: icon || null, description: description || null, visibility }, accessToken)
        toast.success(t('manage_spaces.updated') || 'Space updated')
      } else {
        const data: SpaceCreate = { name: name.trim(), icon: icon || null, description: description || null, ordering: spaces.length, visibility }
        await createSpace(communityUuid, data, accessToken)
        toast.success(t('manage_spaces.created') || 'Space created')
      }
      resetForm()
      refreshSpaces()
    } catch (err: any) {
      toast.error(err.message || t('manage_spaces.save_error') || 'Failed to save space')
    } finally {
      setIsSaving(false)
    }
  }

  const handleDelete = async (spaceUuid: string) => {
    if (!accessToken) return
    try {
      await deleteSpace(spaceUuid, accessToken)
      toast.success(t('manage_spaces.deleted') || 'Space deleted')
      setDeleteConfirm(null)
      refreshSpaces()
    } catch (err: any) {
      toast.error(err.message || t('manage_spaces.delete_error') || 'Failed to delete space')
    }
  }

  const handleDragEnd = async (result: any) => {
    const { source, destination, draggableId } = result
    if (!destination || source.index === destination.index) return

    const reordered = Array.from(spaces)
    const [moved] = reordered.splice(source.index, 1)
    reordered.splice(destination.index, 0, moved)
    const spaceUuids = reordered.map(s => s.space_uuid)

    try {
      const res = await fetch(`${getAPIUrl()}communities/${communityUuid}/spaces/reorder`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${accessToken}` },
        body: JSON.stringify({ space_uuids: spaceUuids }),
      })
      if (!res.ok) throw new Error('Reorder failed')
      refreshSpaces()
    } catch (err: any) {
      toast.error(err.message || 'Failed to reorder spaces')
    }
  }

  return (
    <Modal
      isDialogOpen={isOpen}
      onOpenChange={(open) => { if (!open) { onClose(); resetForm() } }}
      dialogTitle={t('manage_spaces.title') || 'Manage Spaces'}
      dialogDescription={t('manage_spaces.description') || 'Create, edit, reorder, and delete spaces'}
      minWidth="lg"
      dialogContent={
        <div className="space-y-4">
          {/* Existing spaces list */}
          {isLoading ? (
            <div className="flex justify-center py-8">
              <Loader2 size={20} className="animate-spin text-gray-400" />
            </div>
          ) : spaces.length === 0 ? (
            <p className="text-sm text-gray-500 text-center py-4">{t('manage_spaces.no_spaces') || 'No spaces yet'}</p>
          ) : (
            <DragDropContext onDragEnd={handleDragEnd}>
              <Droppable droppableId="spaces">
                {(provided) => (
                  <div ref={provided.innerRef} {...provided.droppableProps} className="space-y-2">
                    {spaces.map((space, index) => (
                      <Draggable key={space.space_uuid} draggableId={space.space_uuid} index={index}>
                        {(provided, snapshot) => (
                          <div
                            ref={provided.innerRef}
                            {...provided.draggableProps}
                            className={`flex items-center gap-2 px-3 py-2.5 bg-white border border-gray-200 rounded-lg ${snapshot.isDragging ? 'opacity-50 shadow-lg' : ''}`}
                          >
                            <button {...provided.dragHandleProps} className="cursor-grab text-gray-400 hover:text-gray-600" aria-label="Drag to reorder">
                              <GripVertical size={16} />
                            </button>
                            <span className="text-base">{space.icon || '💬'}</span>
                            <span className="flex-1 text-sm font-medium text-gray-900">{space.name}</span>
                            <span className={`text-xs px-2 py-0.5 rounded-full ${
                              space.visibility === 'public' ? 'bg-green-50 text-green-700' :
                              space.visibility === 'members' ? 'bg-blue-50 text-blue-700' :
                              'bg-amber-50 text-amber-700'
                            }`}>
                              {space.visibility}
                            </span>
                            <button onClick={() => {
                              setEditingSpace(space)
                              setName(space.name)
                              setIcon(space.icon || '')
                              setDescription(space.description || '')
                              setVisibility(space.visibility)
                            }} className="p-1.5 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-md transition-colors" aria-label="Edit space">
                              <Pencil size={14} />
                            </button>
                            <button onClick={() => setDeleteConfirm(space.space_uuid)} className="p-1.5 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-md transition-colors" aria-label="Delete space">
                              <Trash2 size={14} />
                            </button>
                          </div>
                        )}
                      </Draggable>
                    ))}
                    {provided.placeholder}
                  </div>
                )}
              </Droppable>
            </DragDropContext>
          )}

          {/* Delete confirmation */}
          {deleteConfirm && (
            <div className="flex items-center gap-2 p-3 bg-red-50 border border-red-100 rounded-lg">
              <AlertCircle size={16} className="text-red-500 shrink-0" />
              <span className="text-sm text-red-700 flex-1">{t('manage_spaces.delete_confirm') || 'Delete this space? Discussions will be unassigned.'}</span>
              <button onClick={() => handleDelete(deleteConfirm)} className="px-3 py-1 text-xs font-medium bg-red-600 text-white rounded-md hover:bg-red-700">Delete</button>
              <button onClick={() => setDeleteConfirm(null)} className="px-3 py-1 text-xs font-medium text-gray-600 hover:bg-gray-100 rounded-md">Cancel</button>
            </div>
          )}

          {/* Create / Edit form */}
          {(isCreateOpen || editingSpace) && (
            <div className="border border-gray-200 rounded-lg p-4 space-y-3 bg-gray-50">
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">{t('manage_spaces.name') || 'Name'} *</label>
                <input type="text" value={name} onChange={e => setName(e.target.value)} className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none" placeholder="Space name" />
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">{t('manage_spaces.icon') || 'Icon (emoji)'}</label>
                <input type="text" value={icon} onChange={e => setIcon(e.target.value)} className="w-16 px-3 py-2 text-sm border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none text-center" placeholder="💬" maxLength={2} />
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">{t('manage_spaces.description') || 'Description'}</label>
                <input type="text" value={description} onChange={e => setDescription(e.target.value)} className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none" placeholder="Brief description" />
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">{t('manage_spaces.visibility') || 'Visibility'}</label>
                <select value={visibility} onChange={e => setVisibility(e.target.value)} className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none bg-white">
                  {VISIBILITY_OPTIONS.map(o => (
                    <option key={o.value} value={o.value}>{o.label}</option>
                  ))}
                </select>
              </div>
              <div className="flex justify-end gap-2 pt-2">
                <button onClick={resetForm} className="px-3 py-1.5 text-xs font-medium text-gray-600 hover:bg-gray-200 rounded-md transition-colors">
                  {t('manage_spaces.cancel') || 'Cancel'}
                </button>
                <button onClick={handleSave} disabled={isSaving || !name.trim()} className="px-3 py-1.5 text-xs font-medium text-white bg-gray-900 hover:bg-gray-800 rounded-md transition-colors disabled:opacity-50 flex items-center gap-1">
                  {isSaving && <Loader2 size={12} className="animate-spin" />}
                  {editingSpace ? (t('manage_spaces.save') || 'Save') : (t('manage_spaces.create') || 'Create')}
                </button>
              </div>
            </div>
          )}

          {/* Add button */}
          {!isCreateOpen && !editingSpace && (
            <button onClick={() => setIsCreateOpen(true)} className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-100 rounded-lg transition-colors w-full border border-dashed border-gray-300">
              <Plus size={16} />
              {t('manage_spaces.add_space') || 'Add Space'}
            </button>
          )}
        </div>
      }
    />
  )
}

export default ManageSpacesModal
