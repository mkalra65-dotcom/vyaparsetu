export type ServiceType = "gst_registration" | "fssai_registration" | "udyam_registration";

export type ApplicationStatus =
  | "draft"
  | "documents_pending"
  | "under_review"
  | "clarification_required"
  | "approved"
  | "rejected";

export type User = {
  id: number;
  email: string;
  full_name: string | null;
  is_active: boolean;
  is_admin: boolean;
  created_at: string;
  updated_at: string;
};

export type Application = {
  id: number;
  title: string;
  description: string | null;
  service_type: ServiceType;
  status: ApplicationStatus;
  business_name: string;
  proprietor_name: string | null;
  applicant_mobile: string | null;
  applicant_email: string | null;
  pan_number: string | null;
  aadhaar_number: string | null;
  business_address: string | null;
  city: string | null;
  pincode: string | null;
  state: string | null;
  business_type: string | null;
  business_constitution: string | null;
  nature_of_business: string | null;
  principal_place_of_business: string | null;
  bank_account_details: string | null;
  expected_turnover: string | null;
  annual_turnover: string | null;
  food_business_type: string | null;
  food_category: string | null;
  premises_address: string | null;
  license_type_suggestion: string | null;
  fssai_license_category: string | null;
  enterprise_name: string | null;
  type_of_organisation: string | null;
  major_activity: string | null;
  nic_code: string | null;
  enterprise_type: string | null;
  investment_amount: string | null;
  turnover: string | null;
  customer_clarification_message: string | null;
  internal_admin_notes: string | null;
  health_score: number | null;
  ai_review_summary: string | null;
  required_documents: string[];
  missing_required_documents: string[];
  owner_id: number;
  created_at: string;
  updated_at: string;
};

export type DocumentMetadata = {
  id: number;
  application_id: number;
  document_type: string;
  original_filename: string;
  stored_filename: string;
  file_path: string;
  mime_type: string;
  file_size: number;
  uploaded_by_user_id: number;
  ai_processing_status: "pending" | "processed" | "manual_review";
  requires_attention: boolean;
  created_at: string;
};

export type ApplicationPayload = Partial<Application> & {
  title: string;
  service_type: ServiceType;
  business_name: string;
};

export type AuditLog = {
  id: number;
  application_id: number;
  actor_user_id: number;
  action: string;
  old_status: string | null;
  new_status: string | null;
  note: string | null;
  created_at: string;
};

export type DocumentExtraction = {
  id: number;
  document_id: number;
  provider: string;
  document_type: string;
  extracted_json: {
    document_type: string;
    extracted_fields: Record<string, string>;
    confidence_score: number;
    validation_warnings: string[];
    extracted_at: string;
  };
  confidence_score: number;
  validation_warnings: string[];
  created_at: string;
};

export type AdminDocumentMetadata = DocumentMetadata & {
  extractions: DocumentExtraction[];
};

export type AdminApplicationDetail = Application & {
  documents: AdminDocumentMetadata[];
  audit_logs: AuditLog[];
};

export type AdminApplicationListResponse = {
  items: Application[];
  total: number;
  page: number;
  page_size: number;
};

export type AdminMetrics = {
  total_applications: number;
  gst_applications: number;
  fssai_applications: number;
  udyam_applications: number;
  documents_pending: number;
  under_review: number;
  clarification_required: number;
  approved: number;
  rejected: number;
};

export type AdminApplicationFilters = {
  service_type?: ServiceType;
  status?: ApplicationStatus;
  search?: string;
  created_from?: string;
  created_to?: string;
  page?: number;
  page_size?: number;
};

export type Notification = {
  id: number;
  user_id: number | null;
  application_id: number | null;
  channel: string;
  event_type: string;
  recipient: string;
  subject: string;
  message: string;
  status: string;
  provider: string;
  provider_message_id: string | null;
  error_message: string | null;
  is_read: boolean;
  created_at: string;
  sent_at: string | null;
  read_at: string | null;
};

export type LeadStatus = "new" | "contacted" | "qualified" | "converted" | "lost";

export type Lead = {
  id: number;
  name: string;
  mobile: string;
  email: string | null;
  service_interest: ServiceType;
  message: string | null;
  status: LeadStatus;
  created_at: string;
  updated_at: string;
};

export type Pricing = Record<ServiceType, { label: string; price: string }>;

export type AdminAnalytics = {
  leads: number;
  applications: number;
  conversion_rate: number;
  applications_by_service: Partial<Record<ServiceType, number>>;
  approved_applications: number;
  revenue_placeholder: string;
};
