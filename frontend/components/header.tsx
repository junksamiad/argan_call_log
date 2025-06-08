"use client"

import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Button } from "@/components/ui/button"
import { Menu, RefreshCw, ArrowLeft } from "lucide-react"
import { useState } from "react"
import { AdminPanel } from "./admin-panel"

interface HeaderProps {
  showSearchButtons?: boolean
  onRefresh?: () => void
  onBackToCallLog?: () => void
}

export function Header({ showSearchButtons = false, onRefresh, onBackToCallLog }: HeaderProps = {}) {
  const [isAdminPanelOpen, setIsAdminPanelOpen] = useState(false)

  return (
    <header className="bg-white shadow-sm border-b border-gray-200">
      <div className="container mx-auto px-4 py-8">
        <div className="flex items-center justify-between">
          <div className="flex items-center">
            <Avatar className="h-20 w-20 border-2 border-gray-200">
              <AvatarImage
                src="https://res.cloudinary.com/dgaiaqf8x/image/upload/t_Banner 16:9/v1748800579/IMG-20240627-WA0000-2_ekivgv.jpg"
                alt="Argan Consultancy Logo"
              />
              <AvatarFallback>AC</AvatarFallback>
            </Avatar>
            <div className="ml-6">
              <h1 className="text-2xl font-bold text-gray-800">Argan Consultancy</h1>
              <p className="text-sm text-gray-500">Call Log Management System</p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {showSearchButtons && (
              <>
                <Button onClick={onRefresh} variant="outline" size="sm" className="transition-all hover:bg-gray-100">
                  <RefreshCw className="w-4 h-4 mr-2" />
                  Refresh
                </Button>
                <Button
                  onClick={onBackToCallLog}
                  variant="outline"
                  size="sm"
                  className="transition-all hover:bg-gray-100"
                >
                  <ArrowLeft className="w-4 h-4 mr-2" />
                  Back to Call Log
                </Button>
              </>
            )}
            <Button variant="outline" size="icon" onClick={() => setIsAdminPanelOpen(true)} className="ml-auto">
              <Menu className="h-5 w-5" />
              <span className="sr-only">Open admin panel</span>
            </Button>
          </div>
        </div>
      </div>

      <AdminPanel isOpen={isAdminPanelOpen} onClose={() => setIsAdminPanelOpen(false)} />
    </header>
  )
}
