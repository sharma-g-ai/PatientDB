// API configuration and base URL handling
const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000';

class ApiService {
  private baseURL: string;

  constructor() {
    this.baseURL = API_BASE_URL;
    console.log('API Base URL:', this.baseURL);
  }

  private getFullUrl(endpoint: string): string {
    // Remove leading slash if present to avoid double slashes
    const cleanEndpoint = endpoint.startsWith('/') ? endpoint.slice(1) : endpoint;
    return `${this.baseURL}/${cleanEndpoint}`;
  }

  async makeRequest(endpoint: string, options?: RequestInit): Promise<Response> {
    const url = this.getFullUrl(endpoint);
    
    const defaultOptions: RequestInit = {
      headers: {
        'Content-Type': 'application/json',
      },
    };

    // Merge options, but don't override Content-Type for FormData
    const mergedOptions = { ...defaultOptions, ...options };
    
    // Remove Content-Type for FormData requests
    if (options?.body instanceof FormData) {
      delete (mergedOptions.headers as any)?.['Content-Type'];
    }

    try {
      const response = await fetch(url, mergedOptions);
      
      // Log response status for debugging
      if (!response.ok) {
        console.error(`API Error: ${response.status} for ${url}`);
      }
      
      return response;
    } catch (error) {
      console.error(`API request failed for ${url}:`, error);
      throw error;
    }
  }

  // Health check to verify backend is accessible
  async healthCheck(): Promise<boolean> {
    try {
      const response = await this.makeRequest('health');
      return response.ok;
    } catch (error) {
      console.error('Backend health check failed:', error);
      return false;
    }
  }

  // Chat API methods
  async startChatSession(): Promise<Response> {
    return this.makeRequest('api/chat/start-session', {
      method: 'POST',
    });
  }

  async sendChatMessage(sessionId: string, query: string, patientContext?: string): Promise<Response> {
    const formData = new FormData();
    formData.append('session_id', sessionId);
    formData.append('query', query);
    if (patientContext) {
      formData.append('patient_context', patientContext);
    }

    return this.makeRequest('api/chat/chat', {
      method: 'POST',
      body: formData,
    });
  }

  async uploadFile(sessionId: string, file: File): Promise<Response> {
    const formData = new FormData();
    formData.append('session_id', sessionId);
    formData.append('file', file);

    return this.makeRequest('api/chat/upload-file', {
      method: 'POST',
      body: formData,
    });
  }

  async getSessionFiles(sessionId: string): Promise<Response> {
    return this.makeRequest(`api/chat/session/${sessionId}/files`);
  }

  // Document API methods
  async uploadDocuments(files: File[]): Promise<any> {
    const formData = new FormData();
    files.forEach(file => {
      formData.append('files', file);
    });

    const response = await this.makeRequest('api/documents/upload', {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      throw new Error(`Failed to upload documents: ${response.statusText}`);
    }

    return response.json();
  }

  // Patient API methods
  async createPatient(patientData: any): Promise<any> {
    const response = await this.makeRequest('api/patients/', {
      method: 'POST',
      body: JSON.stringify(patientData),
    });

    if (!response.ok) {
      throw new Error(`Failed to create patient: ${response.statusText}`);
    }

    return response.json();
  }

  async updatePatient(patientId: string, patientData: any): Promise<any> {
    const response = await this.makeRequest(`api/patients/${patientId}`, {
      method: 'PUT',
      body: JSON.stringify(patientData),
    });

    if (!response.ok) {
      throw new Error(`Failed to update patient: ${response.statusText}`);
    }

    return response.json();
  }

  async getPatients(): Promise<any> {
    const response = await this.makeRequest('api/patients/');
    
    if (!response.ok) {
      throw new Error(`Failed to fetch patients: ${response.statusText}`);
    }

    return response.json();
  }

  async deletePatient(patientId: string): Promise<void> {
    const response = await this.makeRequest(`api/patients/${patientId}`, {
      method: 'DELETE',
    });

    if (!response.ok) {
      throw new Error(`Failed to delete patient: ${response.statusText}`);
    }
  }
}

// Export singleton instance
export const apiService = new ApiService();

// Legacy exports for compatibility
export const documentsApi = {
  uploadDocuments: (files: File[]) => apiService.uploadDocuments(files)
};

export const patientsApi = {
  createPatient: (data: any) => apiService.createPatient(data),
  updatePatient: (id: string, data: any) => apiService.updatePatient(id, data),
  getPatients: () => apiService.getPatients(),
  deletePatient: (id: string) => apiService.deletePatient(id)
};