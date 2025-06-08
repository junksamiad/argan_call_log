"use client"

import { useRouter } from "next/navigation"
import { Header } from "@/components/header"
import { SearchInterface } from "@/components/search-interface"

export default function SearchPage() {
  const router = useRouter()

  const handleRefresh = () => {
    // This will be passed to SearchInterface to trigger refresh
    window.location.reload()
  }

  const handleBackToCallLog = () => {
    router.push("/")
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Header showSearchButtons={true} onRefresh={handleRefresh} onBackToCallLog={handleBackToCallLog} />
      <main className="container mx-auto py-8 px-4">
        <SearchInterface />
      </main>
    </div>
  )
}
