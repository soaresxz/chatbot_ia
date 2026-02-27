export interface Conversation {
  id: string
  name: string
  initials: string
  phone: string
  lastMessage: string
  time: string
  status: "bot" | "humano"
  unread: number
}
