export type Device = {
  id: string;
  name: string;
  device_type: string;
  is_active: boolean;
  created_at: string;
};

export type Household = {
  id: string;
  name: string;
  location?: string | null;
  owner_id: string;
  devices: Device[];
  created_at: string;
};
