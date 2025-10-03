import { useQuery, useMutation, useQueryClient } from 'react-query'
import { authApi, userManagementApi } from '@/services/api'
import type {
  LoginRequest,
  UserProfile,
  ChangePasswordRequest,
  UserCreateRequest,
  UserUpdateRequest
} from '@/types'

// Auth hooks
export function useLogin() {
  return useMutation(
    (credentials: LoginRequest) => authApi.login(credentials).then(res => res.data),
    {
      onSuccess: (data) => {
        localStorage.setItem('token', data.access_token)
        localStorage.setItem('user', JSON.stringify(data.user))
        window.location.href = '/'
      },
    }
  )
}

export function useLogout() {
  const queryClient = useQueryClient()
  return useMutation(
    () => authApi.logout().then(res => res.data),
    {
      onSuccess: () => {
        localStorage.removeItem('token')
        localStorage.removeItem('user')
        queryClient.clear()
        window.location.href = '/login'
      },
    }
  )
}

export function useCurrentUser() {
  return useQuery(
    'currentUser',
    () => authApi.getProfile().then(res => res.data),
    {
      retry: false,
      staleTime: 5 * 60 * 1000, // 5 minutes
    }
  )
}

export function useUpdateProfile() {
  const queryClient = useQueryClient()
  return useMutation(
    (data: Partial<UserProfile>) => authApi.updateProfile(data).then(res => res.data),
    {
      onSuccess: (data) => {
        queryClient.setQueryData('currentUser', data)
        localStorage.setItem('user', JSON.stringify(data))
      },
    }
  )
}

export function useChangePassword() {
  return useMutation(
    (data: ChangePasswordRequest) => authApi.changePassword(data).then(res => res.data)
  )
}

export function useUserSessions() {
  return useQuery(
    'userSessions',
    () => authApi.getSessions().then(res => res.data),
    {
      refetchInterval: 30000, // Refresh every 30 seconds
    }
  )
}

export function useRevokeSession() {
  const queryClient = useQueryClient()
  return useMutation(
    (sessionId: string) => authApi.revokeSession(sessionId).then(res => res.data),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('userSessions')
      },
    }
  )
}

export function useUserActivity() {
  return useQuery(
    'userActivity',
    () => authApi.getActivity({ limit: 50 }).then(res => res.data)
  )
}

export function useVerifyToken() {
  return useQuery(
    'verifyToken',
    () => authApi.verifyToken().then(res => res.data),
    {
      retry: false,
      refetchInterval: 5 * 60 * 1000, // Check every 5 minutes
    }
  )
}

// User Management hooks (Admin only)
export function useUsers(params?: {
  skip?: number;
  limit?: number;
  search?: string;
  is_active?: boolean;
  is_admin?: boolean;
}) {
  return useQuery(
    ['users', params],
    () => userManagementApi.listUsers(params).then(res => res.data),
    {
      keepPreviousData: true,
    }
  )
}

export function useUser(userId: string) {
  return useQuery(
    ['user', userId],
    () => userManagementApi.getUser(userId).then(res => res.data),
    {
      enabled: !!userId,
    }
  )
}

export function useCreateUser() {
  const queryClient = useQueryClient()
  return useMutation(
    (data: UserCreateRequest) => userManagementApi.createUser(data).then(res => res.data),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('users')
      },
    }
  )
}

export function useUpdateUser() {
  const queryClient = useQueryClient()
  return useMutation(
    ({ userId, data }: { userId: string; data: UserUpdateRequest }) =>
      userManagementApi.updateUser(userId, data).then(res => res.data),
    {
      onSuccess: (data) => {
        queryClient.invalidateQueries('users')
        queryClient.setQueryData(['user', data.id], data)
      },
    }
  )
}

export function useDeleteUser() {
  const queryClient = useQueryClient()
  return useMutation(
    (userId: string) => userManagementApi.deleteUser(userId).then(res => res.data),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('users')
      },
    }
  )
}

export function useResetUserPassword() {
  return useMutation(
    ({ userId, newPassword }: { userId: string; newPassword?: string }) =>
      userManagementApi.resetUserPassword(userId, newPassword).then(res => res.data)
  )
}

export function useUpdateUserDatabaseAccess() {
  const queryClient = useQueryClient()
  return useMutation(
    ({ userId, databases }: { userId: string; databases: string[] }) =>
      userManagementApi.updateUserDatabaseAccess(userId, databases).then(res => res.data),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('users')
      },
    }
  )
}

export function useActivityLogs(params?: {
  skip?: number;
  limit?: number;
  user_id?: string;
  activity_type?: string;
}) {
  return useQuery(
    ['activityLogs', params],
    () => userManagementApi.getActivityLogs(params).then(res => res.data),
    {
      keepPreviousData: true,
    }
  )
}

export function useUserStats() {
  return useQuery(
    'userStats',
    () => userManagementApi.getUserStats().then(res => res.data)
  )
}

// Auth utilities
export function getStoredUser(): UserProfile | null {
  try {
    const user = localStorage.getItem('user')
    return user ? JSON.parse(user) : null
  } catch {
    return null
  }
}

export function getStoredToken(): string | null {
  return localStorage.getItem('token')
}

export function isAuthenticated(): boolean {
  const token = getStoredToken()
  const user = getStoredUser()
  return !!(token && user)
}

export function isAdmin(): boolean {
  const user = getStoredUser()
  return user?.is_admin || false
}