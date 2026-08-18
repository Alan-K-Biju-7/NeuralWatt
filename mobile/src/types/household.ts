export type Device = {
  id: string;
  name: string;
  device_type: string;
  brand?: string | null;
  model?: string | null;
  rated_power_watts: number;
  location?: string | null;
  device_key?: string | null;
  is_active: boolean;
  created_at: string;
};

export type Household = {
  id: string;
  name: string;
  address?: string | null;
  area_sqft?: number | null;
  num_occupants?: number | null;
  owner_id: string;
  devices: Device[];
  created_at: string;
};
