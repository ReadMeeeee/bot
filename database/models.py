from sqlalchemy import BigInteger, String, Boolean, ForeignKey, Integer, JSON
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, create_async_engine


# Создание асинхронного движка базы данных
engine = create_async_engine(url='sqlite+aiosqlite:///db.sqlite3', echo=True)
async_session = async_sessionmaker(engine, expire_on_commit=False)


# Базовый класс
class Base(AsyncAttrs, DeclarativeBase):
    pass

# Добавить старосту
# Таблица групп
class Group(Base):
    __tablename__ = 'groups'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)           # Суррогатный ID группы в БД
    group_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False)  # Телеграм ID группы

    group_name: Mapped[str] = mapped_column(String, nullable=False)     # Название группы
    group_course: Mapped[int] = mapped_column(Integer, nullable=False)  # Курс группы
    group_number: Mapped[int] = mapped_column(Integer, nullable=False)  # Номер группы

    tg_link: Mapped[str] = mapped_column(String, nullable=True)  # Ссылка на группу в Telegram

    schedule: Mapped[dict] = mapped_column(JSON, nullable=True) # Строка с расписанием группы

    students = relationship("Student", back_populates="group")  # Связь с таблицей студентов


# Таблица студентов (без избыточных данных о группе!!!)
class Student(Base):
    __tablename__ = 'students'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)  # Суррогатный ID студента

    student_tg_id: Mapped[int] = mapped_column(BigInteger, nullable=False)             # Телеграм ID студента
    student_username: Mapped[str] = mapped_column(String, unique=True, nullable=True)  # @username студента
    student_full_name: Mapped[str] = mapped_column(String, nullable=False)             # ФИ студента
    student_is_leader: Mapped[bool] = mapped_column(Boolean, default=False)            # Является ли старостой

    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id"), nullable=False)  # Внешний ключ на группу

    group = relationship("Group", back_populates="students")  # Связь с таблицей групп