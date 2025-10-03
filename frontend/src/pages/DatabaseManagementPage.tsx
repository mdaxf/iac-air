import { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Tab } from '@headlessui/react'
import {
  CircleStackIcon,
  TableCellsIcon,
  ChartBarIcon,
  DocumentTextIcon,
  TagIcon,
  BeakerIcon,
  Cog6ToothIcon,
  ArrowLeftIcon
} from '@heroicons/react/24/outline'

// Tab panels
import EntitiesPanel from '@/components/database-management/EntitiesPanel'
import MetricsPanel from '@/components/database-management/MetricsPanel'
import TemplatesPanel from '@/components/database-management/TemplatesPanel'
import MappingsPanel from '@/components/database-management/MappingsPanel'
import TablesPanel from '@/components/database-management/TablesPanel'
import DocumentsPanel from '@/components/database-management/DocumentsPanel'
import SettingsPanel from '@/components/database-management/SettingsPanel'

function classNames(...classes: string[]) {
  return classes.filter(Boolean).join(' ')
}

export default function DatabaseManagementPage() {
  const { dbAlias } = useParams<{ dbAlias: string }>()
  const navigate = useNavigate()

  if (!dbAlias) {
    navigate('/databases')
    return null
  }

  const tabs = [
    { name: 'Business Entities', icon: CircleStackIcon, component: EntitiesPanel },
    { name: 'Business Metrics', icon: ChartBarIcon, component: MetricsPanel },
    { name: 'Query Templates', icon: BeakerIcon, component: TemplatesPanel },
    { name: 'Concept Mappings', icon: TagIcon, component: MappingsPanel },
    { name: 'Table Metadata', icon: TableCellsIcon, component: TablesPanel },
    { name: 'Vector Documents', icon: DocumentTextIcon, component: DocumentsPanel },
    { name: 'Settings & Sync', icon: Cog6ToothIcon, component: SettingsPanel },
  ]

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="sm:flex sm:items-center sm:justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">
            Semantic Layer: <span className="text-primary-600">{dbAlias}</span>
          </h1>
          <p className="mt-2 text-sm text-gray-700">
            Manage business entities, metrics, templates, and semantic metadata for this database
          </p>
        </div>
        <div className="mt-4 sm:mt-0">
          <button
            className="btn btn-secondary"
            onClick={() => navigate('/databases')}
          >
            <ArrowLeftIcon className="h-4 w-4 mr-2" />
            Back to Databases
          </button>
        </div>
      </div>

      <Tab.Group>
        <Tab.List className="flex space-x-1 rounded-xl bg-blue-900/20 p-1">
          {tabs.map((tab) => (
            <Tab
              key={tab.name}
              className={({ selected }) =>
                classNames(
                  'w-full rounded-lg py-2.5 text-sm font-medium leading-5',
                  'ring-white ring-opacity-60 ring-offset-2 ring-offset-blue-400 focus:outline-none focus:ring-2',
                  selected
                    ? 'bg-white text-blue-700 shadow'
                    : 'text-blue-700 hover:bg-white/[0.12] hover:text-blue-800'
                )
              }
            >
              <div className="flex items-center justify-center space-x-2">
                <tab.icon className="h-5 w-5" />
                <span>{tab.name}</span>
              </div>
            </Tab>
          ))}
        </Tab.List>
        <Tab.Panels className="mt-6">
          {tabs.map((tab, idx) => (
            <Tab.Panel
              key={idx}
              className={classNames(
                'rounded-xl bg-white p-6',
                'ring-white ring-opacity-60 ring-offset-2 ring-offset-blue-400 focus:outline-none focus:ring-2'
              )}
            >
              <tab.component dbAlias={dbAlias} />
            </Tab.Panel>
          ))}
        </Tab.Panels>
      </Tab.Group>
    </div>
  )
}
