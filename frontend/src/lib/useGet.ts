import { useQuery } from "@tanstack/react-query";
import { get } from "@/api/client";

export function useGet<T>(key: string, path: string) {
  return useQuery<T>({ queryKey: [key], queryFn: () => get<T>(path), staleTime: 0 });
}
