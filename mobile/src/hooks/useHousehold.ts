import { useQuery } from "@tanstack/react-query";
import { householdService } from "@/services/households";

export function useHousehold() {
  const query = useQuery({ queryKey: ["household", "mine"], queryFn: householdService.mine });
  return {
    ...query,
    household: query.data,
    device: query.data?.devices.find((item) => item.is_active) ?? query.data?.devices[0],
  };
}
