import { Fragment } from 'react'
import { Listbox, Transition } from '@headlessui/react'
import { CheckIcon, ChevronUpDownIcon, CircleStackIcon } from '@heroicons/react/24/outline'
import clsx from 'clsx'
import type { DatabaseConnection } from '@/types'

interface DatabaseSelectorProps {
  databases: DatabaseConnection[]
  selected: string
  onSelect: (alias: string) => void
  disabled?: boolean
}

export default function DatabaseSelector({ databases, selected, onSelect, disabled = false }: DatabaseSelectorProps) {
  const selectedDb = databases.find(db => db.alias === selected)

  return (
    <div className="w-64">
      <Listbox value={selected} onChange={disabled ? () => {} : onSelect} disabled={disabled}>
        <div className="relative">
          <Listbox.Button className={clsx(
            "relative w-full rounded-lg py-2 pl-3 pr-10 text-left shadow-md focus:outline-none sm:text-sm border",
            disabled
              ? "cursor-not-allowed bg-gray-100 border-gray-200 text-gray-500"
              : "cursor-default bg-white border-gray-300 focus-visible:border-primary-500 focus-visible:ring-2 focus-visible:ring-white focus-visible:ring-opacity-75 focus-visible:ring-offset-2 focus-visible:ring-offset-primary-300"
          )}>
            <span className="flex items-center">
              <CircleStackIcon className={clsx("h-5 w-5 mr-2", disabled ? "text-gray-300" : "text-gray-400")} />
              <span className="block truncate">
                {selectedDb ? selectedDb.alias : 'Select database...'}
                {disabled && selectedDb && <span className="ml-2 text-xs">(locked)</span>}
              </span>
            </span>
            {!disabled && (
              <span className="pointer-events-none absolute inset-y-0 right-0 flex items-center pr-2">
                <ChevronUpDownIcon className="h-5 w-5 text-gray-400" aria-hidden="true" />
              </span>
            )}
          </Listbox.Button>
          <Transition
            as={Fragment}
            leave="transition ease-in duration-100"
            leaveFrom="opacity-100"
            leaveTo="opacity-0"
          >
            <Listbox.Options className="absolute mt-1 max-h-60 w-full overflow-auto rounded-md bg-white py-1 text-base shadow-lg ring-1 ring-black ring-opacity-5 focus:outline-none sm:text-sm z-10">
              {databases.length === 0 ? (
                <div className="relative cursor-default select-none py-2 px-4 text-gray-700">
                  No databases connected
                </div>
              ) : (
                databases.map((database) => (
                  <Listbox.Option
                    key={database.alias}
                    className={({ active }) =>
                      clsx(
                        'relative cursor-default select-none py-2 pl-10 pr-4',
                        active ? 'bg-primary-100 text-primary-900' : 'text-gray-900'
                      )
                    }
                    value={database.alias}
                  >
                    {({ selected }) => (
                      <>
                        <div className="flex items-center">
                          <div className="flex-shrink-0">
                            <div className={clsx(
                              'h-2 w-2 rounded-full',
                              database.is_active ? 'bg-green-400' : 'bg-red-400'
                            )} />
                          </div>
                          <div className="ml-3">
                            <span className={clsx(
                              'block truncate',
                              selected ? 'font-medium' : 'font-normal'
                            )}>
                              {database.alias}
                            </span>
                            <span className="text-xs text-gray-500">
                              {database.type} • {database.host}
                            </span>
                          </div>
                        </div>
                        {selected ? (
                          <span className="absolute inset-y-0 left-0 flex items-center pl-3 text-primary-600">
                            <CheckIcon className="h-5 w-5" aria-hidden="true" />
                          </span>
                        ) : null}
                      </>
                    )}
                  </Listbox.Option>
                ))
              )}
            </Listbox.Options>
          </Transition>
        </div>
      </Listbox>
    </div>
  )
}