import React, { useState } from 'react';
import { X } from 'lucide-react';
import { InspectionItem } from '../../types';

interface CreateTemplateModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (template: {
    name: string;
    description: string;
    items: InspectionItem[];
  }) => void;
}

export function CreateTemplateModal({ isOpen, onClose, onSubmit }: CreateTemplateModalProps) {
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [items, setItems] = useState<InspectionItem[]>([]);
  const [newItem, setNewItem] = useState({
    title: '',
    type: 'checkbox' as const,
    required: false,
    options: '',
  });

  const handleAddItem = () => {
    const item: InspectionItem = {
      id: crypto.randomUUID(),
      title: newItem.title,
      type: newItem.type,
      required: newItem.required,
      options: newItem.type === 'select' ? newItem.options.split(',').map(o => o.trim()) : undefined,
    };
    setItems([...items, item]);
    setNewItem({
      title: '',
      type: 'checkbox',
      required: false,
      options: '',
    });
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit({
      name,
      description,
      items,
    });
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-lg max-w-2xl w-full p-6">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-semibold">Create New Template</h2>
          <button onClick={onClose} className="text-gray-500 hover:text-gray-700">
            <X className="w-5 h-5" />
          </button>
        </div>
        
        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label className="block text-sm font-medium text-gray-700">Template Name</label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">Description</label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
              rows={3}
            />
          </div>

          <div>
            <h3 className="text-lg font-medium mb-2">Inspection Items</h3>
            <div className="space-y-4">
              {items.map((item, index) => (
                <div key={item.id} className="flex items-center space-x-2 p-2 bg-gray-50 rounded">
                  <span className="font-medium">{index + 1}.</span>
                  <span>{item.title}</span>
                  <span className="text-sm text-gray-500">({item.type})</span>
                  <button
                    type="button"
                    onClick={() => setItems(items.filter(i => i.id !== item.id))}
                    className="text-red-500 hover:text-red-700 ml-auto"
                  >
                    <X className="w-4 h-4" />
                  </button>
                </div>
              ))}
            </div>

            <div className="mt-4 space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700">Item Title</label>
                  <input
                    type="text"
                    value={newItem.title}
                    onChange={(e) => setNewItem({ ...newItem, title: e.target.value })}
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Type</label>
                  <select
                    value={newItem.type}
                    onChange={(e) => setNewItem({ ...newItem, type: e.target.value as any })}
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                  >
                    <option value="checkbox">Checkbox</option>
                    <option value="text">Text</option>
                    <option value="number">Number</option>
                    <option value="select">Select</option>
                  </select>
                </div>
              </div>

              {newItem.type === 'select' && (
                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    Options (comma-separated)
                  </label>
                  <input
                    type="text"
                    value={newItem.options}
                    onChange={(e) => setNewItem({ ...newItem, options: e.target.value })}
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                    placeholder="Option 1, Option 2, Option 3"
                  />
                </div>
              )}

              <div className="flex items-center">
                <input
                  type="checkbox"
                  checked={newItem.required}
                  onChange={(e) => setNewItem({ ...newItem, required: e.target.checked })}
                  className="rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                />
                <label className="ml-2 text-sm text-gray-700">Required</label>
              </div>

              <button
                type="button"
                onClick={handleAddItem}
                disabled={!newItem.title}
                className="w-full bg-gray-100 text-gray-700 py-2 px-4 rounded-md hover:bg-gray-200 disabled:opacity-50"
              >
                Add Item
              </button>
            </div>
          </div>

          <div className="flex justify-end space-x-4">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={!name || items.length === 0}
              className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 disabled:opacity-50"
            >
              Create Template
            </button>
          </div>
        </form>
      </div>
    </div>
  );
} 