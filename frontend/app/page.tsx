import { Header } from "@/components/header"
import CallLogData from "@/components/call-log-data"

export default function Home() {
  return (
    <div className="min-h-screen bg-gray-50">
      <Header />
      <main className="container mx-auto py-8 px-4">
        <CallLogData />
      </main>
    </div>
  )
}
