import type { ParsedContent } from '@nuxt/content'
import type { Avatar, Badge, Link } from '#ui/types'

export interface BlogPost extends ParsedContent {
  title: string
  description: string
  date: string
  image?: HTMLImageElement
  badge?: Badge
  authors?: ({
    name: string
    description?: string
    avatar: Avatar
  } & Link)[]
}

export interface User {
  id: number
  email: string
  username: string
  first_name?: string
  last_name?: string
  phone?: string
  avatar?: string
  avatar_url?: string
  display_name?: string
  specialty?: string
  specialty_id?: number | null
  bio?: string
  city?: string
  service_address?: string
  service_address_lat?: number
  service_address_lon?: number
  is_email_verified?: boolean
  /** Кнопка «Расписание» на публичной странице записи */
  show_public_schedule?: boolean
  show_public_reviews?: boolean
  show_public_portfolio?: boolean
  created_at?: string
  updated_at?: string
  /** effective для дней без явной записи WorkSchedule; см. workScheduleTemplate */
  work_schedule_template?: string
  /** Минимальный срок до записи для клиентов */
  booking_lead?: string
  shift_cycle?: string
  shift_anchor_date?: string | null
  subscription?: UserSubscription
}

export interface UserSubscriptionOffers {
  firstMonthBonusAvailable: boolean
  firstYearBonusAvailable: boolean
  monthPriceRub: number
  yearPriceRub: number
  yearDiscountRub: number
}

export interface UserSubscription {
  plan: 'free' | 'pro'
  effectivePlan: 'free' | 'pro'
  planLabel: string
  storedPlanLabel: string
  expiresAt: string | null
  startedAt: string | null
  isActive: boolean
  isTrial: boolean
  grantedVia: 'trial' | 'admin' | 'payment' | null
  daysRemaining: number | null
  offers?: UserSubscriptionOffers
  limits: {
    maxCustomers: number
    maxBookingsPerMonth: number
    maxServices: number
  }
}

export interface Customer {
  id: number
  user?: number
  name: string
  email: string
  phone?: string
  avatar?: string
  status?: 'regular' | 'loyal' | 'vip' | 'first-time'
  /** If true, `status` overrides auto rules from visits_count */
  status_manual?: boolean
  notes?: string
  visits_count?: number
  last_visit_date?: string | null
  next_booking_date?: string | null
  next_booking_time?: string | null
  created_at?: string
  updated_at?: string
}

export interface CustomerHistoryItem {
  id: number
  date: string
  startTime: string
  serviceName: string
  price: number
  status: string
  isUpcoming: boolean
}

export interface Service {
  id: number
  user?: number
  name: string
  description?: string
  duration: number
  price: number
  prepayment?: number
  sort_order?: number
  cover_image?: string
  cover_image_url?: string
  portfolio_images?: ServiceImage[]
  active?: boolean
  created_at?: string
  updated_at?: string
}

export interface ServiceImage {
  id: number
  service?: number
  image?: string
  image_url?: string
  order?: number
  created_at?: string
}

export interface Event {
  id: number
  user?: number
  service?: number
  serviceId?: number | null
  serviceName?: string
  name: string
  description?: string
  date: string
  startTime: string
  duration: number
  maxParticipants?: number
  bookedSlots?: number
  price?: number
  created_at?: string
  updated_at?: string
}

export interface Booking {
  id: number
  user?: number
  customer?: number
  customerId?: number
  customerName?: string
  service?: number
  serviceId?: number
  serviceName?: string
  event?: number
  eventId?: number
  date: string
  startTime: string
  endTime: string
  status?: 'pending' | 'confirmed' | 'completed' | 'cancelled'
  notes?: string
  created_at?: string
  updated_at?: string
}

export interface WorkBreak {
  id?: number
  startTime: string
  endTime: string
}

export interface WorkSchedule {
  id?: number
  user?: number
  date: string
  type: 'workday' | 'nonworkday' | 'sickleave' | 'vacation'
  startTime?: string
  endTime?: string
  breaks?: WorkBreak[]
}

export interface ScheduleTemplate {
  id?: number
  user?: number
  name: string
  type: 'workday' | 'dayoff' | 'vacation'
  startTime?: string
  endTime?: string
  breaks?: WorkBreak[]
  daysOfWeek?: number[] // 0-6, где 0 = воскресенье
}

export interface Review {
  id: number
  user?: number
  customer?: number
  customerName?: string
  service?: number
  serviceId?: number
  serviceName?: string
  rating: number // 1-5
  comment?: string
  photos?: string[]
  reply?: string
  replyAuthor?: string
  created_at?: string
  updated_at?: string
}

export type Period = 'daily' | 'weekly' | 'monthly'

export interface Range {
  start: Date
  end: Date
}

export interface Stat {
  title: string
  icon: string
  value: string | number
  variation: number
  to?: string
}

export interface AnalyticsMetric {
  value: number
  variation: number
  previousValue?: number
}

export interface AnalyticsStatsResponse {
  newClients: AnalyticsMetric
  regularClients: AnalyticsMetric
  bookings: AnalyticsMetric
  completedBookings: AnalyticsMetric
}

export interface AnalyticsRevenuePoint {
  date: string
  amount: number
}

export type AnalyticsRevenueMode = 'actual' | 'potential'

export interface AnalyticsRevenueResponse {
  total: number
  points: AnalyticsRevenuePoint[]
  mode?: AnalyticsRevenueMode
}

export interface AnalyticsBreakdownItem {
  label: string
  value: number
}

export interface AnalyticsServiceBreakdownSection {
  total: number
  items: AnalyticsBreakdownItem[]
}

export interface AnalyticsServicesBreakdownResponse {
  bookingsByService: AnalyticsServiceBreakdownSection
  revenueByService: AnalyticsServiceBreakdownSection
}

export interface AnalyticsDualRevenuePoint {
  date: string
  received: number
  expected: number
}

export interface AnalyticsPeriodSummary {
  averageCheck: number
  cancellations: number
  returningClients: number
  bookingsCount: number
  trendReady: boolean
  trendHint: string | null
}

export interface AnalyticsClientsBreakdown {
  total: number
  new: number
  returning: number
  regular: number
  items: AnalyticsBreakdownItem[]
}

export interface AnalyticsOverviewResponse {
  revenue: AnalyticsMetric
  bookings: AnalyticsMetric
  newClients: AnalyticsMetric
  completedBookings: AnalyticsMetric
  successRate: number
  periodSummary: AnalyticsPeriodSummary
  clientsBreakdown: AnalyticsClientsBreakdown
  revenueByService: AnalyticsServiceBreakdownSection
  revenueChart: {
    totalReceived: number
    totalExpected: number
    points: AnalyticsDualRevenuePoint[]
  }
  previousRange: { start: string, end: string }
}

export interface AnalyticsInsight {
  icon: string
  text: string
}

export interface AnalyticsLoadByDay {
  day: string
  weekday: number
  loadPercent: number
  availableMinutes: number
  bookedMinutes: number
}

export interface AnalyticsPopularService {
  name: string
  bookings: number
  revenue: number
}

export interface AnalyticsLoadResponse {
  load: AnalyticsMetric
  freeSlots: AnalyticsMetric
  bookings: AnalyticsMetric
  revenue: AnalyticsMetric
  heatmap: {
    hours: string[]
    days: string[]
    cells: number[][]
    max: number
  }
  loadByDay: AnalyticsLoadByDay[]
  insights: AnalyticsInsight[]
  popularServices: AnalyticsPopularService[]
  previousRange: { start: string, end: string }
}
