"use client"

import { useState, useEffect } from "react"
import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle } from "@/components/ui/sheet"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Loader2, Plus, Pencil, Trash2, AlertCircle } from "lucide-react"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"

interface StaffMember {
  id: string
  name: string
}

interface AdminPanelProps {
  isOpen: boolean
  onClose: () => void
}

export function AdminPanel({ isOpen, onClose }: AdminPanelProps) {
  const [staffMembers, setStaffMembers] = useState<StaffMember[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Dialog states
  const [isAddDialogOpen, setIsAddDialogOpen] = useState(false)
  const [isEditDialogOpen, setIsEditDialogOpen] = useState(false)
  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false)
  const [selectedStaff, setSelectedStaff] = useState<StaffMember | null>(null)
  const [newStaffName, setNewStaffName] = useState("")
  const [isSaving, setIsSaving] = useState(false)

  // Fetch staff members when the panel opens
  useEffect(() => {
    if (isOpen) {
      fetchStaffMembers()
    }
  }, [isOpen])

  const fetchStaffMembers = async () => {
    try {
      setLoading(true)
      setError(null)

      const response = await fetch("/api/staff")

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const data = await response.json()
      setStaffMembers(data.staffMembers || [])
    } catch (err) {
      console.error("Error fetching staff members:", err)
      setError("Failed to load staff members. Please try again.")
    } finally {
      setLoading(false)
    }
  }

  const handleAddStaff = async () => {
    if (!newStaffName.trim()) return

    try {
      setIsSaving(true)

      const response = await fetch("/api/staff", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ name: newStaffName }),
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      await fetchStaffMembers()
      setIsAddDialogOpen(false)
      setNewStaffName("")
    } catch (err) {
      console.error("Error adding staff member:", err)
      alert("Failed to add staff member. Please try again.")
    } finally {
      setIsSaving(false)
    }
  }

  const handleEditStaff = async () => {
    if (!selectedStaff || !newStaffName.trim()) return

    try {
      setIsSaving(true)

      const response = await fetch(`/api/staff/${selectedStaff.id}`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ name: newStaffName }),
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      await fetchStaffMembers()
      setIsEditDialogOpen(false)
      setSelectedStaff(null)
      setNewStaffName("")
    } catch (err) {
      console.error("Error updating staff member:", err)
      alert("Failed to update staff member. Please try again.")
    } finally {
      setIsSaving(false)
    }
  }

  const handleDeleteStaff = async () => {
    if (!selectedStaff) return

    try {
      setIsSaving(true)

      const response = await fetch(`/api/staff/${selectedStaff.id}`, {
        method: "DELETE",
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      await fetchStaffMembers()
      setIsDeleteDialogOpen(false)
      setSelectedStaff(null)
    } catch (err) {
      console.error("Error deleting staff member:", err)
      alert("Failed to delete staff member. Please try again.")
    } finally {
      setIsSaving(false)
    }
  }

  const openEditDialog = (staff: StaffMember) => {
    setSelectedStaff(staff)
    setNewStaffName(staff.name)
    setIsEditDialogOpen(true)
  }

  const openDeleteDialog = (staff: StaffMember) => {
    setSelectedStaff(staff)
    setIsDeleteDialogOpen(true)
  }

  return (
    <>
      <Sheet open={isOpen} onOpenChange={onClose}>
        <SheetContent className="sm:max-w-md">
          <SheetHeader>
            <SheetTitle>Admin Panel</SheetTitle>
            <SheetDescription>Manage staff members for Argan Consultancy</SheetDescription>
          </SheetHeader>

          <div className="mt-6 space-y-6">
            <div className="flex justify-between items-center">
              <h3 className="text-lg font-medium">Staff Members</h3>
              <Button onClick={() => setIsAddDialogOpen(true)} size="sm">
                <Plus className="h-4 w-4 mr-1" /> Add Staff
              </Button>
            </div>

            {loading ? (
              <div className="flex justify-center items-center py-8">
                <Loader2 className="h-8 w-8 animate-spin text-gray-400" />
              </div>
            ) : error ? (
              <div className="bg-red-50 border border-red-200 rounded-md p-4 text-red-700 flex items-start">
                <AlertCircle className="h-5 w-5 mr-2 flex-shrink-0" />
                <p>{error}</p>
              </div>
            ) : staffMembers.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                <p>No staff members found.</p>
                <p className="text-sm mt-1">Click "Add Staff" to create your first staff member.</p>
              </div>
            ) : (
              <div className="border rounded-md overflow-hidden">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Name</TableHead>
                      <TableHead className="w-[100px] text-right">Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {staffMembers.map((staff) => (
                      <TableRow key={staff.id}>
                        <TableCell className="font-medium">{staff.name}</TableCell>
                        <TableCell className="text-right">
                          <div className="flex justify-end gap-2">
                            <Button variant="ghost" size="icon" onClick={() => openEditDialog(staff)}>
                              <Pencil className="h-4 w-4" />
                              <span className="sr-only">Edit</span>
                            </Button>
                            <Button
                              variant="ghost"
                              size="icon"
                              onClick={() => openDeleteDialog(staff)}
                              className="text-red-500 hover:text-red-600 hover:bg-red-50"
                            >
                              <Trash2 className="h-4 w-4" />
                              <span className="sr-only">Delete</span>
                            </Button>
                          </div>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            )}
          </div>
        </SheetContent>
      </Sheet>

      {/* Add Staff Dialog */}
      <Dialog open={isAddDialogOpen} onOpenChange={setIsAddDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Add New Staff Member</DialogTitle>
            <DialogDescription>Enter the name of the new staff member.</DialogDescription>
          </DialogHeader>

          <div className="py-4">
            <Input
              placeholder="Staff Name"
              value={newStaffName}
              onChange={(e) => setNewStaffName(e.target.value)}
              className="w-full"
            />
          </div>

          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => {
                setIsAddDialogOpen(false)
                setNewStaffName("")
              }}
              disabled={isSaving}
            >
              Cancel
            </Button>
            <Button onClick={handleAddStaff} disabled={!newStaffName.trim() || isSaving}>
              {isSaving ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Saving...
                </>
              ) : (
                "Add Staff"
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Edit Staff Dialog */}
      <Dialog open={isEditDialogOpen} onOpenChange={setIsEditDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Edit Staff Member</DialogTitle>
            <DialogDescription>Update the name of the staff member.</DialogDescription>
          </DialogHeader>

          <div className="py-4">
            <Input
              placeholder="Staff Name"
              value={newStaffName}
              onChange={(e) => setNewStaffName(e.target.value)}
              className="w-full"
            />
          </div>

          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => {
                setIsEditDialogOpen(false)
                setSelectedStaff(null)
                setNewStaffName("")
              }}
              disabled={isSaving}
            >
              Cancel
            </Button>
            <Button onClick={handleEditStaff} disabled={!newStaffName.trim() || isSaving}>
              {isSaving ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Saving...
                </>
              ) : (
                "Save Changes"
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete Staff Dialog */}
      <Dialog open={isDeleteDialogOpen} onOpenChange={setIsDeleteDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete Staff Member</DialogTitle>
            <DialogDescription>
              Are you sure you want to delete {selectedStaff?.name}? This action cannot be undone.
            </DialogDescription>
          </DialogHeader>

          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => {
                setIsDeleteDialogOpen(false)
                setSelectedStaff(null)
              }}
              disabled={isSaving}
            >
              Cancel
            </Button>
            <Button variant="destructive" onClick={handleDeleteStaff} disabled={isSaving}>
              {isSaving ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Deleting...
                </>
              ) : (
                "Delete"
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  )
}
