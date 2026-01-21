import api from '@/lib/api';

export interface Person {
    id: number;
    first_name: string;
    last_name: string;
    external_number: string;
}

export interface PersonCreate {
    first_name: string;
    last_name: string;
    external_number: string;
}

export const getPersons = async () => {
    const response = await api.get<Person[]>('/persons');
    return response.data;
};

export const createPerson = async (data: PersonCreate) => {
    const response = await api.post<Person>('/persons', data);
    return response.data;
};

export const deletePerson = async (id: number) => {
    const response = await api.delete(`/persons/${id}`);
    return response.data;
};
