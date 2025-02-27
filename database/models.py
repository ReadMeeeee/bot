from sqlalchemy import BigInteger, String, Boolean, ForeignKey, Integer
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, create_async_engine


# Создание асинхронного движка базы данных
engine = create_async_engine(url='sqlite+aiosqlite:///db.sqlite3', echo=True)
async_session = async_sessionmaker(engine, expire_on_commit=False)


# Базовый класс
class Base(AsyncAttrs, DeclarativeBase):
    pass


# Таблица групп
class Group(Base):
    __tablename__ = 'groups'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, nullable=False)  # Название группы (ПМИ, ФИИТ, и т.д.)
    number: Mapped[int] = mapped_column(Integer, nullable=False)  # Номер группы (1, 2, 6 и т.д.)
    tg_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False)  # Телеграм ID группы
    tg_link: Mapped[str] = mapped_column(String, nullable=True)  # Ссылка на группу в Telegram
    bot_name: Mapped[str] = mapped_column(String, nullable=True) # Имя бота

    students = relationship("Student", back_populates="group")  # Связь с таблицей студентов


# Таблица студентов
class Student(Base):
    __tablename__ = 'students'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    tg_id: Mapped[int] = mapped_column(BigInteger, nullable=False)  # Телеграм ID студента
    username: Mapped[str] = mapped_column(String, unique=True, nullable=True)  # Телеграм username (@username)
    full_name: Mapped[str] = mapped_column(String, nullable=False)  # ФИО студента
    is_leader: Mapped[bool] = mapped_column(Boolean, default=False)  # Староста или нет
    course: Mapped[str] = mapped_column(String, nullable=False)  # Курс (Бакалавриат 1, Магистратура 2 и т.д.)
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id"), nullable=False)  # Внешний ключ на группу

    group = relationship("Group", back_populates="students")  # Связь с таблицей групп
