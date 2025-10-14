# Полная синхронизация
db = next(get_db())
result = UnifiedSyncService.sync_all(db)

# Или отдельно
teacher_service = TeacherSyncService()
teacher_result = teacher_service.sync_teachers(db)

student_service = StudentSyncService()
student_result = student_service.sync_students(db)