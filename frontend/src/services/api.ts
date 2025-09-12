import axios from 'axios';
import { Patient, PatientCreate, PatientUpdate, DocumentProcessingResult, ChatMessage, ChatResponse } from '../types';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Documents API
export const documentsApi = {
  uploadDocument: async (file: File): Promise<DocumentProcessingResult> => {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await api.post('/api/documents/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  getSupportedTypes: async () => {
    const response = await api.get('/api/documents/supported-types');
    return response.data;
  },
};

// Patients API
export const patientsApi = {
  createPatient: async (patientData: PatientCreate): Promise<Patient> => {
    const response = await api.post('/api/patients/', patientData);
    return response.data;
  },

  getAllPatients: async (): Promise<Patient[]> => {
    const response = await api.get('/api/patients/');
    return response.data;
  },

  getPatient: async (patientId: string): Promise<Patient> => {
    const response = await api.get(`/api/patients/${patientId}`);
    return response.data;
  },

  updatePatient: async (patientId: string, patientData: PatientUpdate): Promise<Patient> => {
    const response = await api.put(`/api/patients/${patientId}`, patientData);
    return response.data;
  },

  deletePatient: async (patientId: string): Promise<void> => {
    await api.delete(`/api/patients/${patientId}`);
  },
};

// Chat API
export const chatApi = {
  sendMessage: async (message: ChatMessage): Promise<ChatResponse> => {
    const response = await api.post('/api/chat/', message);
    return response.data;
  },

  refreshKnowledgeBase: async (): Promise<void> => {
    await api.post('/api/chat/refresh-knowledge-base');
  },
};

export default api;
