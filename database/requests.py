from sqlalchemy.future import select
from database.models import Student, Group, async_session

# Добавление новой группы
async def add_group(tg_id: int, name: str, course: int, number: int, link: str):
    async with async_session() as session:
        async with session.begin():
            group = Group(
                group_id=tg_id,
                group_name=name,
                group_course=course,
                group_number=number,
                tg_link=link
            )
            session.add(group)
        await session.commit()

# Добавление студента
async def add_student(tg_id: int, username: str, full_name: str, is_leader: bool, group_id: int):
    async with async_session() as session:
        async with session.begin():
            student = Student(
                student_tg_id=tg_id,
                student_username=username,
                student_full_name=full_name,
                student_is_leader=is_leader,
                group_id=group_id
            )
            session.add(student)
        await session.commit()

# Удаление студента по username
async def delete_student(username: str):
    async with async_session() as session:
        async with session.begin():
            result = await session.execute(select(Student).filter_by(student_username=username))
            student = result.scalar()
            if student:
                await session.delete(student)
                await session.commit()
                return f"✅ Студент {username} удален!"
            return f"❌ Студент {username} не найден."

# Назначение нового старосты
async def update_leader(username: str):
    async with async_session() as session:
        async with session.begin():
            result = await session.execute(select(Student).filter_by(student_username=username))
            student = result.scalar()
            if student:
                # Снимаем статус старосты с остальных студентов группы
                await session.execute(
                    select(Student)
                    .filter(Student.group_id == student.group_id, Student.student_is_leader.is_(True))
                    .execution_options(synchronize_session=False)
                )
                # Обновляем данные нового старосты
                student.student_is_leader = True
                await session.commit()
                return f"✅ Студент {username} назначен старостой!"
            return f"❌ Студент {username} не найден."

# Получение студента по Telegram ID
async def get_student_by_tg_id(tg_id: int):
    async with async_session() as session:
        result = await session.execute(select(Student).filter_by(student_tg_id=tg_id))
        return result.scalar()

# Получение группы по Telegram ID
async def get_group_by_tg_id(tg_id: int):
    async with async_session() as session:
        result = await session.execute(select(Group).filter_by(group_id=tg_id))
        return result.scalar()

# Проверка, является ли студент старостой
async def is_leader(tg_id: int):
    student = await get_student_by_tg_id(tg_id)
    return student.student_is_leader if student else False

# Получение списка студентов группы
async def get_students_by_group(group_id: int):
    async with async_session() as session:
        result = await session.execute(select(Student).filter_by(group_id=group_id))
        return result.scalars().all()
