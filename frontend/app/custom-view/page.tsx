import { Suspense } from "react"
import { Header } from "@/components/header"
import { CustomDataView } from "@/components/custom-data-view"
import { Skeleton } from "@/components/ui/skeleton"

export default function CustomViewPage() {
  return (
    <div className="min-h-screen bg-gray-50">
      <Header />
      <main className="container mx-auto py-8 px-4">
        <div className="max-w-6xl mx-auto">
          <Suspense fallback={<CustomViewSkeleton />}>
            <CustomDataView />
          </Suspense>
        </div>
      </main>
    </div>
  )
}

function CustomViewSkeleton() {
  return (
    <div className="space-y-4">
      <Skeleton className="h-8 w-1/3" />
      <div className="grid gap-4">
        {[...Array(3)].map((_, i) => (
          <div key={i} className="border rounded-lg p-4">
            <Skeleton className="h-6 w-1/4 mb-4" />
            <div className="space-y-2">
              <Skeleton className="h-4 w-full" />
              <Skeleton className="h-4 w-3/4" />
              <Skeleton className="h-4 w-5/6" />
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
