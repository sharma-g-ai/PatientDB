import React, { useState } from 'react';
import { PatientCreate, PatientUpdate } from '../types';

interface PatientFormProps {
  initialData?: PatientCreate;
  onSubmit: (data: PatientCreate | PatientUpdate) => void;
  onCancel?: () => void;
  isSubmitting?: boolean;
  title?: string;
}

const PatientForm: React.FC<PatientFormProps> = ({
  initialData,
  onSubmit,
  onCancel,
  isSubmitting = false,
  title = 'Patient Information'
}) => {
  const [formData, setFormData] = useState<PatientCreate>({
    name: initialData?.name || '',
    date_of_birth: initialData?.date_of_birth || '',
    diagnosis: initialData?.diagnosis || '',
    prescription: initialData?.prescription || ''
  });

  const [errors, setErrors] = useState<{ [key: string]: string }>({});

  const validateForm = (): boolean => {
    const newErrors: { [key: string]: string } = {};

    if (!formData.name.trim()) {
      newErrors.name = 'Name is required';
    }

    if (!formData.date_of_birth.trim()) {
      newErrors.date_of_birth = 'Date of birth is required';
    } else {
      // Basic date format validation
      const dateRegex = /^\d{4}-\d{2}-\d{2}$/;
      if (!dateRegex.test(formData.date_of_birth)) {
        newErrors.date_of_birth = 'Date must be in YYYY-MM-DD format';
      }
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    if (validateForm()) {
      onSubmit(formData);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));

    // Clear error when user starts typing
    if (errors[name]) {
      setErrors(prev => ({
        ...prev,
        [name]: ''
      }));
    }
  };

  return (
    <div className="bg-white p-6 rounded-lg shadow-lg max-w-2xl mx-auto">
      <h2 className="text-2xl font-bold mb-6 text-gray-800">{title}</h2>
      
      <form onSubmit={handleSubmit} className="space-y-6">
        <div>
          <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-2">
            Patient Name *
          </label>
          <input
            type="text"
            id="name"
            name="name"
            value={formData.name}
            onChange={handleChange}
            className={`w-full px-3 py-2 border rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500 ${
              errors.name ? 'border-red-500' : 'border-gray-300'
            }`}
            placeholder="Enter patient's full name"
          />
          {errors.name && <p className="mt-1 text-sm text-red-600">{errors.name}</p>}
        </div>

        <div>
          <label htmlFor="date_of_birth" className="block text-sm font-medium text-gray-700 mb-2">
            Date of Birth *
          </label>
          <input
            type="date"
            id="date_of_birth"
            name="date_of_birth"
            value={formData.date_of_birth}
            onChange={handleChange}
            className={`w-full px-3 py-2 border rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500 ${
              errors.date_of_birth ? 'border-red-500' : 'border-gray-300'
            }`}
          />
          {errors.date_of_birth && <p className="mt-1 text-sm text-red-600">{errors.date_of_birth}</p>}
        </div>

        <div>
          <label htmlFor="diagnosis" className="block text-sm font-medium text-gray-700 mb-2">
            Diagnosis
          </label>
          <textarea
            id="diagnosis"
            name="diagnosis"
            value={formData.diagnosis}
            onChange={handleChange}
            rows={3}
            className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
            placeholder="Enter medical diagnosis or condition"
          />
        </div>

        <div>
          <label htmlFor="prescription" className="block text-sm font-medium text-gray-700 mb-2">
            Prescription
          </label>
          <textarea
            id="prescription"
            name="prescription"
            value={formData.prescription}
            onChange={handleChange}
            rows={4}
            className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
            placeholder="Enter prescribed medications and instructions"
          />
        </div>

        <div className="flex justify-end space-x-4">
          {onCancel && (
            <button
              type="button"
              onClick={onCancel}
              className="px-6 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
              disabled={isSubmitting}
            >
              Cancel
            </button>
          )}
          <button
            type="submit"
            disabled={isSubmitting}
            className="px-6 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isSubmitting ? 'Saving...' : 'Save Patient'}
          </button>
        </div>
      </form>
    </div>
  );
};

export default PatientForm;
