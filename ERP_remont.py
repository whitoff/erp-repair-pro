import streamlit as st
import pandas as pd
import datetime
import plotly.express as px
import plotly.graph_objects as go
from io import BytesIO
import base64
import os
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
from enum import Enum
import json
from pathlib import Path
import time
import numpy as np
from datetime import timedelta
import calendar
import warnings

warnings.filterwarnings('ignore')

# ==================== КОНФИГУРАЦИЯ ====================
st.set_page_config(
    page_title="ERP Ремонтный цех Pro",
    page_icon="🔧",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Папка для данных
DATA_FOLDER = Path("erp_data")
DATA_FOLDER.mkdir(exist_ok=True)

# Стилизация
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 15px;
        color: white;
        margin-bottom: 2rem;
        text-align: center;
    }
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        text-align: center;
        transition: transform 0.3s;
    }
    .metric-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.15);
    }
    .stButton > button {
        border-radius: 8px;
        transition: all 0.3s;
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
    .workday-btn {
        background-color: #4CAF50;
        color: white;
        font-weight: bold;
    }
    .calendar-day-work {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 8px;
        padding: 10px;
        text-align: center;
        cursor: pointer;
        transition: all 0.3s;
    }
    .calendar-day-work:hover {
        background-color: #c3e6cb;
        transform: scale(1.02);
    }
    .calendar-day-off {
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        border-radius: 8px;
        padding: 10px;
        text-align: center;
        cursor: pointer;
        transition: all 0.3s;
    }
    .calendar-day-off:hover {
        background-color: #f5c6cb;
        transform: scale(1.02);
    }
    .calendar-day-empty {
        background-color: #f5f5f5;
        border: 1px solid #ddd;
        border-radius: 8px;
        padding: 10px;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)


# ==================== КЛАСС ДЛЯ ЭКСПОРТА ====================
class ExportManager:
    """Класс для экспорта данных в различные форматы"""

    @staticmethod
    def export_to_excel(data, filename, sheet_name="Данные"):
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            data.to_excel(writer, index=False, sheet_name=sheet_name)
        return output.getvalue()

    @staticmethod
    def export_to_csv(data, filename):
        return data.to_csv(index=False).encode('utf-8')

    @staticmethod
    def export_analytics(repairs_df, spare_parts_df, employees_df, period):
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            if len(repairs_df) > 0:
                repairs_stats = repairs_df.groupby('status').size().reset_index(name='количество')
                repairs_stats.to_excel(writer, sheet_name='Статусы ремонтов', index=False)
                type_stats = repairs_df['repair_type'].value_counts().reset_index()
                type_stats.columns = ['Тип ремонта', 'Количество']
                type_stats.to_excel(writer, sheet_name='Типы ремонтов', index=False)
                priority_stats = repairs_df['priority'].value_counts().reset_index()
                priority_stats.columns = ['Приоритет', 'Количество']
                priority_stats.to_excel(writer, sheet_name='Приоритеты', index=False)

            if len(spare_parts_df) > 0:
                spare_parts_df.to_excel(writer, sheet_name='Запчасти', index=False)

            if len(employees_df) > 0:
                employees_df.to_excel(writer, sheet_name='Сотрудники', index=False)

            info_df = pd.DataFrame([{
                'Период': period,
                'Дата выгрузки': datetime.datetime.now().strftime('%d.%m.%Y %H:%M:%S'),
                'Всего ремонтов': len(repairs_df),
                'Завершено': len(repairs_df[repairs_df['status'] == 'Завершен']) if len(repairs_df) > 0 else 0,
                'В работе': len(repairs_df[repairs_df['status'] == 'В работе']) if len(repairs_df) > 0 else 0
            }])
            info_df.to_excel(writer, sheet_name='Информация', index=False)

        return output.getvalue()

    @staticmethod
    def export_warehouse(spare_parts_df):
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            spare_parts_df.to_excel(writer, sheet_name='Все запчасти', index=False)
            low_stock = spare_parts_df[spare_parts_df['stock'] <= spare_parts_df['order_point']]
            if len(low_stock) > 0:
                low_stock.to_excel(writer, sheet_name='Дефицит', index=False)
            stats_df = pd.DataFrame([{
                'Всего запчастей': len(spare_parts_df),
                'Дефицит': len(low_stock),
                'Общий остаток': spare_parts_df['stock'].sum(),
                'Дата выгрузки': datetime.datetime.now().strftime('%d.%m.%Y %H:%M:%S')
            }])
            stats_df.to_excel(writer, sheet_name='Статистика', index=False)
        return output.getvalue()

    @staticmethod
    def export_report(repairs_df, employees_df, work_days_df, month, year):
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            if len(repairs_df) > 0:
                repairs_df.to_excel(writer, sheet_name=f'Ремонты_{month}_{year}', index=False)

            if len(work_days_df) > 0:
                work_days_df.to_excel(writer, sheet_name='Отработанные дни', index=False)

            if len(employees_df) > 0:
                employee_stats = []
                for _, emp in employees_df.iterrows():
                    emp_repairs = repairs_df[repairs_df['employees'].str.contains(emp['name'], na=False)] if len(
                        repairs_df) > 0 else pd.DataFrame()
                    emp_days = work_days_df[work_days_df['employee'] == emp['name']] if len(
                        work_days_df) > 0 else pd.DataFrame()
                    employee_stats.append({
                        'Сотрудник': emp['name'],
                        'Роль': emp['role'],
                        'Количество ремонтов': len(emp_repairs),
                        'Завершено': len(emp_repairs[emp_repairs['status'] == 'Завершен']) if len(
                            emp_repairs) > 0 else 0,
                        'Отработанных дней': len(emp_days),
                        'ФОТ': len(emp_days) * emp['daily_rate']
                    })
                pd.DataFrame(employee_stats).to_excel(writer, sheet_name='KPI сотрудников', index=False)

            info_df = pd.DataFrame([{
                'Месяц': month,
                'Год': year,
                'Дата создания': datetime.datetime.now().strftime('%d.%m.%Y %H:%M:%S'),
                'Всего ремонтов': len(repairs_df),
                'Завершено': len(repairs_df[repairs_df['status'] == 'Завершен']) if len(repairs_df) > 0 else 0
            }])
            info_df.to_excel(writer, sheet_name='Информация', index=False)
        return output.getvalue()


# ==================== ОСНОВНОЕ ПРИЛОЖЕНИЕ ====================
class RepairERP:
    """Главный класс приложения"""

    def __init__(self):
        self.export_manager = ExportManager()
        self.init_session_state()

    def init_session_state(self):
        """Инициализация session state"""
        # Запчасти
        parts_file = DATA_FOLDER / 'spare_parts.parquet'
        if parts_file.exists():
            st.session_state.spare_parts = pd.read_parquet(parts_file)
        else:
            st.session_state.spare_parts = pd.DataFrame([
                {"name": "Колодки тормозные задние", "stock": 50, "min_stock": 20, "order_point": 30},
                {"name": "Колодки тормозные передние", "stock": 40, "min_stock": 20, "order_point": 30},
                {"name": "Подшипник левый 6200", "stock": 25, "min_stock": 15, "order_point": 25},
                {"name": "Ручка газа", "stock": 15, "min_stock": 10, "order_point": 12},
                {"name": "Контроллер 2G", "stock": 8, "min_stock": 5, "order_point": 6},
            ])

        # Работы
        works_file = DATA_FOLDER / 'works.parquet'
        if works_file.exists():
            st.session_state.works = pd.read_parquet(works_file)
        else:
            works_list = [
                "Замена рамы", "Ремонт электропроводки", "Диагностика электрики",
                "Ремонт iot", "Замена iot", "Замена контроллера", "Замена ручки газа",
                "Замена концевика", "Замена сигнализации", "Замена дисплея",
                "Замена передней фары", "Замена колодок задних", "Замена колодок передних",
                "Прокачка тормозов", "Ремонт суппорта", "Замена подшипников"
            ]
            st.session_state.works = pd.DataFrame({"name": works_list})

        # Сотрудники
        employees_file = DATA_FOLDER / 'employees.parquet'
        if employees_file.exists():
            st.session_state.employees = pd.read_parquet(employees_file)
        else:
            st.session_state.employees = pd.DataFrame([
                {"name": "Алексей Механик", "role": "Механик", "daily_rate": 5000, "can_elec": False},
                {"name": "Борис Универсал", "role": "Механик-электрик", "daily_rate": 7000, "can_elec": True},
                {"name": "Владимир Универсал", "role": "Механик-электрик", "daily_rate": 7000, "can_elec": True},
            ])

        # Ремонты
        repairs_file = DATA_FOLDER / 'repairs.parquet'
        if repairs_file.exists():
            st.session_state.repairs = pd.read_parquet(repairs_file)
        else:
            st.session_state.repairs = pd.DataFrame(columns=[
                'id', 'gos_number', 'date_receipt', 'date_completion', 'status',
                'repair_type', 'priority', 'employees', 'works', 'parts',
                'parts_cost', 'failure_reason', 'comment', 'tags'
            ])

        # Рабочие дни
        workdays_file = DATA_FOLDER / 'work_days.parquet'
        if workdays_file.exists():
            st.session_state.work_days = pd.read_parquet(workdays_file)
        else:
            st.session_state.work_days = pd.DataFrame(columns=[
                'date', 'employee', 'hours_worked', 'repair_ids'
            ])

        # Для отслеживания состояния
        if 'edit_mode' not in st.session_state:
            st.session_state.edit_mode = {}
        if 'selected_calendar_date' not in st.session_state:
            st.session_state.selected_calendar_date = None

    def save_all(self):
        """Сохранение всех данных"""
        try:
            st.session_state.spare_parts.to_parquet(DATA_FOLDER / 'spare_parts.parquet', index=False)
            st.session_state.works.to_parquet(DATA_FOLDER / 'works.parquet', index=False)
            st.session_state.employees.to_parquet(DATA_FOLDER / 'employees.parquet', index=False)
            st.session_state.repairs.to_parquet(DATA_FOLDER / 'repairs.parquet', index=False)
            st.session_state.work_days.to_parquet(DATA_FOLDER / 'work_days.parquet', index=False)
            return True
        except Exception as e:
            st.error(f"Ошибка сохранения: {e}")
            return False

    def delete_repair(self, repair_id):
        """Удаление ремонта"""
        try:
            idx = st.session_state.repairs[st.session_state.repairs['id'] == repair_id].index
            if len(idx) > 0:
                repair = st.session_state.repairs.loc[idx[0]]
                if repair['parts'] and repair['parts'] != '':
                    parts_list = self.parse_parts_list(repair['parts'])
                    for part_name, qty in parts_list:
                        part_idx = st.session_state.spare_parts[
                            st.session_state.spare_parts['name'] == part_name
                            ].index
                        if len(part_idx) > 0:
                            st.session_state.spare_parts.loc[part_idx[0], 'stock'] += qty

                st.session_state.repairs = st.session_state.repairs.drop(idx[0]).reset_index(drop=True)
                self.save_all()
                return True
            return False
        except Exception as e:
            st.error(f"Ошибка удаления: {e}")
            return False

    def complete_repair(self, repair_id):
        """Завершение ремонта"""
        try:
            idx = st.session_state.repairs[st.session_state.repairs['id'] == repair_id].index
            if len(idx) > 0:
                st.session_state.repairs.loc[idx[0], 'status'] = 'Завершен'
                st.session_state.repairs.loc[idx[0], 'date_completion'] = datetime.date.today().isoformat()
                self.save_all()
                return True
            return False
        except Exception as e:
            st.error(f"Ошибка завершения: {e}")
            return False

    def update_repair(self, repair_id, updated_data):
        """Обновление ремонта"""
        try:
            idx = st.session_state.repairs[st.session_state.repairs['id'] == repair_id].index
            if len(idx) > 0:
                for key, value in updated_data.items():
                    st.session_state.repairs.loc[idx[0], key] = value
                self.save_all()
                return True
            return False
        except Exception as e:
            st.error(f"Ошибка обновления: {e}")
            return False

    def parse_parts_list(self, parts_str):
        """Парсинг строки запчастей в список"""
        parts = []
        if parts_str and parts_str != '':
            for item in parts_str.split(','):
                item = item.strip()
                if item and 'x' in item:
                    name, qty = item.rsplit('x', 1)
                    parts.append((name.strip(), int(qty.strip())))
                elif item:
                    parts.append((item, 1))
        return parts

    def format_parts_string(self, parts_list):
        """Форматирование списка запчастей в строку"""
        if not parts_list:
            return ""
        return ", ".join([f"{name} x{qty}" for name, qty in parts_list])

    def add_work_to_repair(self, repair_id, new_work):
        """Добавление работы к ремонту"""
        try:
            idx = st.session_state.repairs[st.session_state.repairs['id'] == repair_id].index
            if len(idx) > 0:
                current_works = st.session_state.repairs.loc[idx[0], 'works']
                if current_works and current_works != '':
                    works_list = [w.strip() for w in current_works.split(',') if w.strip()]
                    if new_work not in works_list:
                        works_list.append(new_work)
                        st.session_state.repairs.loc[idx[0], 'works'] = ", ".join(works_list)
                else:
                    st.session_state.repairs.loc[idx[0], 'works'] = new_work
                self.save_all()
                return True
            return False
        except Exception as e:
            st.error(f"Ошибка добавления работы: {e}")
            return False

    def remove_work_from_repair(self, repair_id, work_to_remove):
        """Удаление работы из ремонта"""
        try:
            idx = st.session_state.repairs[st.session_state.repairs['id'] == repair_id].index
            if len(idx) > 0:
                current_works = st.session_state.repairs.loc[idx[0], 'works']
                if current_works and current_works != '':
                    works_list = [w.strip() for w in current_works.split(',') if w.strip()]
                    if work_to_remove in works_list:
                        works_list.remove(work_to_remove)
                        st.session_state.repairs.loc[idx[0], 'works'] = ", ".join(works_list) if works_list else ""
                self.save_all()
                return True
            return False
        except Exception as e:
            st.error(f"Ошибка удаления работы: {e}")
            return False

    def add_part_to_repair(self, repair_id, part_name, quantity):
        """Добавление запчасти к ремонту"""
        try:
            idx = st.session_state.repairs[st.session_state.repairs['id'] == repair_id].index
            if len(idx) > 0:
                current_parts = self.parse_parts_list(st.session_state.repairs.loc[idx[0], 'parts'])

                found = False
                for i, (name, qty) in enumerate(current_parts):
                    if name == part_name:
                        current_parts[i] = (name, qty + quantity)
                        found = True
                        break

                if not found:
                    current_parts.append((part_name, quantity))

                st.session_state.repairs.loc[idx[0], 'parts'] = self.format_parts_string(current_parts)

                part_idx = st.session_state.spare_parts[st.session_state.spare_parts['name'] == part_name].index
                if len(part_idx) > 0:
                    st.session_state.spare_parts.loc[part_idx[0], 'stock'] -= quantity

                self.save_all()
                return True
            return False
        except Exception as e:
            st.error(f"Ошибка добавления запчасти: {e}")
            return False

    def remove_part_from_repair(self, repair_id, part_name, quantity):
        """Удаление запчасти из ремонта"""
        try:
            idx = st.session_state.repairs[st.session_state.repairs['id'] == repair_id].index
            if len(idx) > 0:
                current_parts = self.parse_parts_list(st.session_state.repairs.loc[idx[0], 'parts'])

                for i, (name, qty) in enumerate(current_parts):
                    if name == part_name:
                        if qty > quantity:
                            current_parts[i] = (name, qty - quantity)
                        else:
                            current_parts.pop(i)
                        break

                st.session_state.repairs.loc[idx[0], 'parts'] = self.format_parts_string(current_parts)

                part_idx = st.session_state.spare_parts[st.session_state.spare_parts['name'] == part_name].index
                if len(part_idx) > 0:
                    st.session_state.spare_parts.loc[part_idx[0], 'stock'] += quantity

                self.save_all()
                return True
            return False
        except Exception as e:
            st.error(f"Ошибка удаления запчасти: {e}")
            return False

    def add_employee(self, name, role, daily_rate):
        """Добавление сотрудника"""
        try:
            new_employee = pd.DataFrame([{
                'name': name,
                'role': role,
                'daily_rate': daily_rate,
                'can_elec': role == "Механик-электрик"
            }])
            st.session_state.employees = pd.concat([st.session_state.employees, new_employee], ignore_index=True)
            self.save_all()
            return True
        except Exception as e:
            st.error(f"Ошибка добавления: {e}")
            return False

    def update_employee(self, old_name, new_name, role, daily_rate):
        """Обновление данных сотрудника"""
        try:
            idx = st.session_state.employees[st.session_state.employees['name'] == old_name].index
            if len(idx) > 0:
                st.session_state.employees.loc[idx[0], 'name'] = new_name
                st.session_state.employees.loc[idx[0], 'role'] = role
                st.session_state.employees.loc[idx[0], 'daily_rate'] = daily_rate
                st.session_state.employees.loc[idx[0], 'can_elec'] = (role == "Механик-электрик")
                self.save_all()
                return True
            return False
        except Exception as e:
            st.error(f"Ошибка обновления: {e}")
            return False

    def delete_employee(self, employee_name):
        """Удаление сотрудника"""
        try:
            st.session_state.employees = st.session_state.employees[
                st.session_state.employees['name'] != employee_name
                ].reset_index(drop=True)
            self.save_all()
            return True
        except Exception as e:
            st.error(f"Ошибка удаления: {e}")
            return False

    def add_repair(self, gos_number, repair_type, priority, employees, failure_reason,
                   works, parts, comment, tags):
        """Добавление нового ремонта"""
        try:
            new_id = len(st.session_state.repairs) + 1

            works_str = ", ".join(works) if works else ""
            parts_str = ", ".join([f"{p} x{q}" for p, q in parts]) if parts else ""
            employees_str = ", ".join(employees) if employees else ""
            tags_str = ", ".join(tags) if tags else ""

            new_repair = pd.DataFrame([{
                'id': new_id,
                'gos_number': gos_number,
                'date_receipt': datetime.date.today().isoformat(),
                'date_completion': '',
                'status': 'В работе',
                'repair_type': repair_type,
                'priority': priority,
                'employees': employees_str,
                'works': works_str,
                'parts': parts_str,
                'parts_cost': 0,
                'failure_reason': failure_reason,
                'comment': comment,
                'tags': tags_str
            }])

            st.session_state.repairs = pd.concat([st.session_state.repairs, new_repair], ignore_index=True)

            for part_name, quantity in parts:
                if part_name:
                    idx = st.session_state.spare_parts[
                        st.session_state.spare_parts['name'] == part_name
                        ].index
                    if len(idx) > 0:
                        st.session_state.spare_parts.loc[idx[0], 'stock'] -= quantity

            self.save_all()
            return True
        except Exception as e:
            st.error(f"Ошибка добавления ремонта: {e}")
            return False

    def add_work_day(self, date, employee, hours_worked=8, repair_ids=""):
        """Добавление отработанного дня"""
        try:
            existing = st.session_state.work_days[
                (st.session_state.work_days['date'] == date.isoformat()) &
                (st.session_state.work_days['employee'] == employee)
                ]
            if len(existing) > 0:
                return False, "Сотрудник уже отметился за этот день"

            new_day = pd.DataFrame([{
                'date': date.isoformat() if isinstance(date, datetime.date) else str(date),
                'employee': employee,
                'hours_worked': hours_worked,
                'repair_ids': repair_ids
            }])
            st.session_state.work_days = pd.concat([st.session_state.work_days, new_day], ignore_index=True)
            self.save_all()
            return True, "Успешно добавлено"
        except Exception as e:
            return False, str(e)

    def delete_work_day(self, work_day_index):
        """Удаление отработанного дня"""
        try:
            st.session_state.work_days = st.session_state.work_days.drop(work_day_index).reset_index(drop=True)
            self.save_all()
            return True
        except Exception as e:
            st.error(f"Ошибка удаления: {e}")
            return False

    def get_parts_forecast(self, target_repairs=200):
        """Прогноз закупок запчастей на основе реального использования"""
        if len(st.session_state.repairs) == 0:
            return pd.DataFrame()

        # Собираем статистику использования запчастей
        parts_usage = {}
        total_repairs_count = len(st.session_state.repairs)

        for _, repair in st.session_state.repairs.iterrows():
            if repair['parts'] and repair['parts'] != '':
                parts_list = self.parse_parts_list(repair['parts'])
                for part_name, qty in parts_list:
                    if part_name not in parts_usage:
                        parts_usage[part_name] = {
                            'total_used': 0,
                            'repairs_with_part': 0
                        }
                    parts_usage[part_name]['total_used'] += qty
                    parts_usage[part_name]['repairs_with_part'] += 1

        # Если нет данных об использовании
        if not parts_usage:
            return pd.DataFrame()

        forecast_data = []
        for part_name, usage in parts_usage.items():
            # Реальное среднее использование на ремонт
            avg_usage_per_repair = usage['total_used'] / total_repairs_count

            # Прогноз на целевое количество ремонтов
            needed_for_target = avg_usage_per_repair * target_repairs

            # Текущий остаток
            part_info = st.session_state.spare_parts[
                st.session_state.spare_parts['name'] == part_name
                ]
            current_stock = part_info['stock'].values[0] if len(part_info) > 0 else 0

            # Рекомендуемая закупка
            recommend = max(0, needed_for_target - current_stock)

            # Процент ремонтов, в которых используется эта запчасть
            usage_percentage = (usage['repairs_with_part'] / total_repairs_count) * 100

            forecast_data.append({
                'Запчасть': part_name,
                'Всего использовано': usage['total_used'],
                'В скольких ремонтах': usage['repairs_with_part'],
                'Процент использования': f"{usage_percentage:.1f}%",
                'Среднее на ремонт': round(avg_usage_per_repair, 2),
                f'На {target_repairs} ремонтов': round(needed_for_target, 0),
                'Текущий остаток': current_stock,
                'Рекомендуемая закупка': round(recommend, 0),
                'Точка заказа': part_info['order_point'].values[0] if len(part_info) > 0 else 0
            })

        # Сортируем по рекомендуемой закупке (самые нужные сверху)
        forecast_df = pd.DataFrame(forecast_data)
        forecast_df = forecast_df.sort_values('Рекомендуемая закупка', ascending=False)

        return forecast_df

    def get_monthly_forecast(self):
        """Прогноз на месяц на основе реальной статистики"""
        if len(st.session_state.repairs) == 0:
            return pd.DataFrame()

        repairs = st.session_state.repairs.copy()
        repairs['date_dt'] = pd.to_datetime(repairs['date_receipt'])
        repairs['month'] = repairs['date_dt'].dt.to_period('M')

        # Среднее количество ремонтов в месяц
        monthly_counts = repairs.groupby('month').size()
        avg_monthly_repairs = monthly_counts.mean() if len(monthly_counts) > 0 else 10
        forecast_months = max(1, int(avg_monthly_repairs))

        # Общая статистика использования
        total_repairs = len(repairs)
        parts_usage = {}

        for _, repair in repairs.iterrows():
            if repair['parts'] and repair['parts'] != '':
                parts_list = self.parse_parts_list(repair['parts'])
                for part_name, qty in parts_list:
                    if part_name not in parts_usage:
                        parts_usage[part_name] = {
                            'total_used': 0,
                            'repairs_with_part': 0
                        }
                    parts_usage[part_name]['total_used'] += qty
                    parts_usage[part_name]['repairs_with_part'] += 1

        if not parts_usage:
            return pd.DataFrame()

        forecast_data = []
        for part_name, usage in parts_usage.items():
            # Реальное среднее использование на ремонт
            avg_usage_per_repair = usage['total_used'] / total_repairs

            # Прогноз на месяц
            needed_monthly = avg_usage_per_repair * forecast_months

            part_info = st.session_state.spare_parts[
                st.session_state.spare_parts['name'] == part_name
                ]
            current_stock = part_info['stock'].values[0] if len(part_info) > 0 else 0

            usage_percentage = (usage['repairs_with_part'] / total_repairs) * 100

            forecast_data.append({
                'Запчасть': part_name,
                'Используется в': f"{usage_percentage:.1f}% ремонтов",
                'Среднее на ремонт': round(avg_usage_per_repair, 2),
                'Прогноз ремонтов в месяц': forecast_months,
                'Необходимо на месяц': round(needed_monthly, 0),
                'Текущий остаток': current_stock,
                'Рекомендуемая закупка': round(max(0, needed_monthly - current_stock), 0)
            })

        return pd.DataFrame(forecast_data)

    def run(self):
        """Запуск приложения"""
        st.markdown("""
        <div class="main-header">
            <h1>🔧 ERP Ремонтный цех PRO</h1>
            <p>Управление ремонтами электровелосипедов</p>
        </div>
        """, unsafe_allow_html=True)

        menu = st.sidebar.radio(
            "📌 Навигация",
            ["📊 Дашборд", "🔧 Ремонты", "👥 Сотрудники", "📦 Склад",
             "📈 Аналитика", "📑 Отчеты", "📅 Отработанные дни", "🏆 KPI сотрудников", "⚙️ Настройки"]
        )

        st.sidebar.markdown("---")
        if st.sidebar.button("💾 Сохранить все данные", use_container_width=True):
            if self.save_all():
                st.sidebar.success("✅ Данные сохранены!")

        if menu == "📊 Дашборд":
            self.show_dashboard()
        elif menu == "🔧 Ремонты":
            self.show_repairs()
        elif menu == "👥 Сотрудники":
            self.show_employees()
        elif menu == "📦 Склад":
            self.show_warehouse()
        elif menu == "📈 Аналитика":
            self.show_analytics()
        elif menu == "📑 Отчеты":
            self.show_reports()
        elif menu == "📅 Отработанные дни":
            self.show_work_days()
        elif menu == "🏆 KPI сотрудников":
            self.show_employee_kpi()
        elif menu == "⚙️ Настройки":
            self.show_settings()

    def show_dashboard(self):
        """Дашборд с расширенной статистикой"""
        st.header("📊 Дашборд")

        col1, col2 = st.columns(2)
        with col1:
            month = st.selectbox("Месяц", range(1, 13), format_func=lambda x: f"{x:02d}", key="dash_month")
        with col2:
            year = st.number_input("Год", value=datetime.date.today().year, min_value=2024, key="dash_year")

        if len(st.session_state.repairs) > 0:
            repairs = st.session_state.repairs.copy()
            repairs['date_dt'] = pd.to_datetime(repairs['date_receipt'])
            period_repairs = repairs[
                (repairs['date_dt'].dt.year == year) &
                (repairs['date_dt'].dt.month == month)
                ]
        else:
            period_repairs = pd.DataFrame()

        if len(st.session_state.work_days) > 0:
            work_days = st.session_state.work_days.copy()
            work_days['date_dt'] = pd.to_datetime(work_days['date'])
            period_days = work_days[
                (work_days['date_dt'].dt.year == year) &
                (work_days['date_dt'].dt.month == month)
                ]
        else:
            period_days = pd.DataFrame()

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("📦 Запчастей", len(st.session_state.spare_parts))
        with col2:
            st.metric("👥 Сотрудников", len(st.session_state.employees))
        with col3:
            total_repairs = len(period_repairs)
            st.metric("🔧 Всего ремонтов", total_repairs)
        with col4:
            completed = len(period_repairs[period_repairs['status'] == 'Завершен']) if len(period_repairs) > 0 else 0
            st.metric("✅ Завершено", completed)

        st.markdown("---")
        st.subheader("📊 Ключевые показатели")

        if len(period_repairs) > 0:
            completed_repairs = period_repairs[period_repairs['status'] == 'Завершен']
            avg_time = 0
            if len(completed_repairs) > 0:
                times = []
                for _, repair in completed_repairs.iterrows():
                    if repair['date_completion']:
                        start = datetime.datetime.strptime(repair['date_receipt'], '%Y-%m-%d')
                        end = datetime.datetime.strptime(repair['date_completion'], '%Y-%m-%d')
                        times.append((end - start).days)
                avg_time = sum(times) / len(times) if times else 0

            urgent = len(period_repairs[period_repairs['priority'] == 'Высокий'])
            urgent_pct = (urgent / len(period_repairs)) * 100

            duplicate_gos = period_repairs['gos_number'].value_counts()
            repeat = len(duplicate_gos[duplicate_gos > 1])
            repeat_pct = (repeat / len(period_repairs['gos_number'].unique())) * 100 if len(period_repairs) > 0 else 0

            deficit = len(st.session_state.spare_parts[
                              st.session_state.spare_parts['stock'] <= st.session_state.spare_parts['order_point']
                              ])

            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("⏱️ Среднее время ремонта", f"{avg_time:.1f} дн.")
            with col2:
                st.metric("🚨 Срочных ремонтов", f"{urgent_pct:.0f}%")
            with col3:
                st.metric("🔄 Повторных обращений", f"{repeat_pct:.0f}%")
            with col4:
                st.metric("📦 Дефицит запчастей", deficit)
        else:
            st.info("Нет данных для отображения KPI")

        st.markdown("---")
        if len(st.session_state.spare_parts) > 0:
            low_stock = st.session_state.spare_parts[
                st.session_state.spare_parts['stock'] <= st.session_state.spare_parts['order_point']
                ]
            if len(low_stock) > 0:
                st.warning(f"⚠️ Внимание! {len(low_stock)} запчастей требуют пополнения:")
                st.dataframe(low_stock[['name', 'stock', 'min_stock', 'order_point']], use_container_width=True)
            else:
                st.success("✅ Все запчасти в достаточном количестве")

    def show_repairs(self):
        """Управление ремонтами"""
        st.header("🔧 Управление ремонтами")

        tab1, tab2, tab3 = st.tabs(["➕ Новый ремонт", "📋 Активные ремонты", "📜 История"])

        with tab1:
            with st.form("new_repair_form", clear_on_submit=True):
                col1, col2 = st.columns(2)

                with col1:
                    gos_number = st.text_input("Госномер *", placeholder="РА201С")
                    repair_type = st.selectbox("Тип ремонта",
                                               ["Закрытие аренды", "ТО", "Механическое повреждение", "Клиентский"])
                    priority = st.selectbox("Приоритет", ["Высокий", "Средний", "Низкий"])
                    employees = st.multiselect("Исполнители *", st.session_state.employees['name'].tolist())
                    tags = st.multiselect("Теги", ["Клиентский", "Закрытие", "Срочный", "Гарантийный"])

                with col2:
                    failure_reason = st.selectbox("Причина",
                                                  ["Падение", "Износ", "Брак", "ДТП", "Закрытие аренды",
                                                   "По вине клиента"])
                    works_options = st.session_state.works['name'].tolist()
                    works = st.multiselect("Выполняемые работы", works_options)
                    comment = st.text_area("Комментарий", height=100)

                st.subheader("🔩 Запчасти")
                parts_options = st.session_state.spare_parts['name'].tolist()
                num_parts = st.number_input("Количество запчастей", 0, 10, 0, key="num_parts")

                parts = []
                for i in range(num_parts):
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        part = st.selectbox(f"Запчасть {i + 1}", [""] + parts_options, key=f"part_{i}")
                    with col2:
                        qty = st.number_input(f"Кол-во", 1, 100, 1, key=f"qty_{i}")
                    if part:
                        parts.append((part, qty))

                st.caption("* - обязательные поля")
                submitted = st.form_submit_button("📥 Принять в ремонт", use_container_width=True)

                if submitted:
                    if not gos_number:
                        st.error("Введите госномер!")
                    elif not employees:
                        st.error("Выберите исполнителей!")
                    else:
                        if self.add_repair(gos_number, repair_type, priority, employees,
                                           failure_reason, works, parts, comment, tags):
                            st.success("✅ Ремонт успешно создан!")
                            st.rerun()
                        else:
                            st.error("Ошибка при создании ремонта!")

        with tab2:
            st.subheader("📋 Активные ремонты")

            if len(st.session_state.repairs) > 0:
                active = st.session_state.repairs[
                    st.session_state.repairs['status'].isin(['В работе', 'Ожидание запчастей'])
                ]

                if len(active) > 0:
                    for idx, repair in active.iterrows():
                        repair_id = repair['id']

                        if f"edit_{repair_id}" not in st.session_state:
                            st.session_state[f"edit_{repair_id}"] = False
                        if f"add_work_{repair_id}" not in st.session_state:
                            st.session_state[f"add_work_{repair_id}"] = False
                        if f"add_part_{repair_id}" not in st.session_state:
                            st.session_state[f"add_part_{repair_id}"] = False

                        with st.expander(f"🚲 {repair['gos_number']} - {repair['repair_type']} (ID: {repair['id']})"):

                            if not st.session_state[f"edit_{repair_id}"]:
                                col1, col2, col3 = st.columns(3)
                                with col1:
                                    st.write(f"**Приоритет:** {repair['priority']}")
                                    st.write(f"**Статус:** {repair['status']}")
                                with col2:
                                    st.write(f"**Исполнители:** {repair['employees']}")
                                    st.write(f"**Причина:** {repair['failure_reason']}")
                                with col3:
                                    st.write(f"**Дата приема:** {repair['date_receipt']}")
                                    st.write(f"**Теги:** {repair.get('tags', '—')}")

                                st.markdown("---")
                                st.subheader("🔧 Выполняемые работы")
                                if repair['works'] and repair['works'] != '':
                                    works_list = [w.strip() for w in repair['works'].split(',') if w.strip()]
                                    for work in works_list:
                                        col1, col2 = st.columns([4, 1])
                                        with col1:
                                            st.write(f"• {work}")
                                        with col2:
                                            if st.button(f"🗑️", key=f"remove_work_{repair_id}_{work}"):
                                                if self.remove_work_from_repair(repair_id, work):
                                                    st.success(f"Работа '{work}' удалена!")
                                                    st.rerun()
                                else:
                                    st.write("Нет добавленных работ")

                                if st.button(f"➕ Добавить работу", key=f"add_work_btn_{repair_id}"):
                                    st.session_state[f"add_work_{repair_id}"] = True
                                    st.rerun()

                                st.markdown("---")
                                st.subheader("🔩 Используемые запчасти")
                                if repair['parts'] and repair['parts'] != '':
                                    parts_list = self.parse_parts_list(repair['parts'])
                                    for part_name, qty in parts_list:
                                        col1, col2, col3 = st.columns([3, 1, 1])
                                        with col1:
                                            st.write(f"• {part_name}")
                                        with col2:
                                            st.write(f"x{qty}")
                                        with col3:
                                            if st.button(f"🗑️", key=f"remove_part_{repair_id}_{part_name}"):
                                                if self.remove_part_from_repair(repair_id, part_name, qty):
                                                    st.success(f"Запчасть '{part_name}' удалена!")
                                                    st.rerun()
                                else:
                                    st.write("Нет добавленных запчастей")

                                if st.button(f"➕ Добавить запчасть", key=f"add_part_btn_{repair_id}"):
                                    st.session_state[f"add_part_{repair_id}"] = True
                                    st.rerun()

                                if repair['comment']:
                                    st.markdown("---")
                                    st.info(f"**Комментарий:** {repair['comment']}")

                                st.markdown("---")
                                col1, col2, col3, col4 = st.columns(4)

                                with col1:
                                    if st.button(f"✏️ Редактировать", key=f"edit_btn_{repair_id}",
                                                 use_container_width=True):
                                        st.session_state[f"edit_{repair_id}"] = True
                                        st.rerun()

                                with col2:
                                    if st.button(f"✅ Завершить", key=f"complete_{repair_id}", use_container_width=True):
                                        if self.complete_repair(repair_id):
                                            st.success("Ремонт завершен!")
                                            st.rerun()

                                with col3:
                                    if st.button(f"🗑️ Удалить", key=f"delete_{repair_id}", use_container_width=True):
                                        if self.delete_repair(repair_id):
                                            st.success("Ремонт удален!")
                                            st.rerun()

                            elif st.session_state[f"add_work_{repair_id}"]:
                                st.subheader("➕ Добавление работы")

                                works_options = st.session_state.works['name'].tolist()
                                new_work = st.selectbox("Выберите работу", works_options,
                                                        key=f"select_work_{repair_id}")

                                col1, col2 = st.columns(2)
                                with col1:
                                    if st.button("✅ Добавить", key=f"confirm_add_work_{repair_id}",
                                                 use_container_width=True):
                                        if self.add_work_to_repair(repair_id, new_work):
                                            st.success(f"Работа '{new_work}' добавлена!")
                                            st.session_state[f"add_work_{repair_id}"] = False
                                            st.rerun()
                                with col2:
                                    if st.button("❌ Отмена", key=f"cancel_add_work_{repair_id}",
                                                 use_container_width=True):
                                        st.session_state[f"add_work_{repair_id}"] = False
                                        st.rerun()

                            elif st.session_state[f"add_part_{repair_id}"]:
                                st.subheader("➕ Добавление запчасти")

                                col1, col2 = st.columns(2)
                                with col1:
                                    parts_options = st.session_state.spare_parts['name'].tolist()
                                    new_part = st.selectbox("Выберите запчасть", parts_options,
                                                            key=f"select_part_{repair_id}")
                                with col2:
                                    part_qty = st.number_input("Количество", 1, 100, 1, key=f"part_qty_{repair_id}")

                                col1, col2 = st.columns(2)
                                with col1:
                                    if st.button("✅ Добавить", key=f"confirm_add_part_{repair_id}",
                                                 use_container_width=True):
                                        part_stock = st.session_state.spare_parts[
                                            st.session_state.spare_parts['name'] == new_part
                                            ]['stock'].values[0]

                                        if part_stock >= part_qty:
                                            if self.add_part_to_repair(repair_id, new_part, part_qty):
                                                st.success(f"Запчасть '{new_part}' x{part_qty} добавлена!")
                                                st.session_state[f"add_part_{repair_id}"] = False
                                                st.rerun()
                                        else:
                                            st.error(f"Недостаточно запчастей! На складе: {part_stock} шт.")
                                with col2:
                                    if st.button("❌ Отмена", key=f"cancel_add_part_{repair_id}",
                                                 use_container_width=True):
                                        st.session_state[f"add_part_{repair_id}"] = False
                                        st.rerun()

                            else:
                                st.subheader("✏️ Редактирование ремонта")

                                col1, col2 = st.columns(2)
                                with col1:
                                    new_gos_number = st.text_input("Госномер", value=repair['gos_number'],
                                                                   key=f"edit_gos_{repair_id}")
                                    new_repair_type = st.selectbox("Тип ремонта",
                                                                   ["Закрытие аренды", "ТО", "Механическое повреждение",
                                                                    "Клиентский"],
                                                                   index=["Закрытие аренды", "ТО",
                                                                          "Механическое повреждение",
                                                                          "Клиентский"].index(repair['repair_type']),
                                                                   key=f"edit_type_{repair_id}")
                                    new_priority = st.selectbox("Приоритет", ["Высокий", "Средний", "Низкий"],
                                                                index=["Высокий", "Средний", "Низкий"].index(
                                                                    repair['priority']),
                                                                key=f"edit_priority_{repair_id}")

                                with col2:
                                    employees_list = st.session_state.employees['name'].tolist()
                                    current_employees = [e.strip() for e in repair['employees'].split(',')] if repair[
                                        'employees'] else []
                                    new_employees = st.multiselect("Исполнители", employees_list,
                                                                   default=[e for e in current_employees if
                                                                            e in employees_list],
                                                                   key=f"edit_employees_{repair_id}")

                                    new_failure_reason = st.selectbox("Причина",
                                                                      ["Падение", "Износ", "Брак", "ДТП",
                                                                       "Закрытие аренды", "По вине клиента"],
                                                                      index=["Падение", "Износ", "Брак", "ДТП",
                                                                             "Закрытие аренды",
                                                                             "По вине клиента"].index(
                                                                          repair['failure_reason']),
                                                                      key=f"edit_reason_{repair_id}")

                                tags_options = ["Клиентский", "Закрытие", "Срочный", "Гарантийный"]
                                current_tags = [t.strip() for t in repair.get('tags', '').split(',')] if repair.get(
                                    'tags') else []
                                new_tags = st.multiselect("Теги", tags_options,
                                                          default=[t for t in current_tags if t in tags_options],
                                                          key=f"edit_tags_{repair_id}")

                                new_comment = st.text_area("Комментарий",
                                                           value=repair['comment'] if repair['comment'] else "",
                                                           key=f"edit_comment_{repair_id}")

                                st.markdown("---")
                                st.subheader("🔧 Работы")

                                current_works = [w.strip() for w in repair['works'].split(',')] if repair[
                                    'works'] else []
                                works_options = st.session_state.works['name'].tolist()
                                edited_works = st.multiselect("Список работ", works_options,
                                                              default=[w for w in current_works if w in works_options],
                                                              key=f"edit_works_{repair_id}")

                                st.markdown("---")
                                st.subheader("🔩 Запчасти")

                                current_parts = self.parse_parts_list(repair['parts'])
                                st.write("**Текущие запчасти:**")
                                if current_parts:
                                    for part_name, qty in current_parts:
                                        st.write(f"• {part_name} x{qty}")
                                else:
                                    st.write("Нет запчастей")

                                st.write("**Редактирование запчастей:**")
                                num_edit_parts = st.number_input("Количество позиций запчастей", 0, 20,
                                                                 value=len(current_parts) if current_parts else 1,
                                                                 key=f"num_edit_parts_{repair_id}")

                                edited_parts = []
                                for i in range(num_edit_parts):
                                    col1, col2, col3 = st.columns([2, 1, 0.5])
                                    default_name = current_parts[i][0] if i < len(current_parts) else (
                                        parts_options[0] if parts_options else "")
                                    default_qty = current_parts[i][1] if i < len(current_parts) else 1

                                    with col1:
                                        default_index = parts_options.index(
                                            default_name) if default_name in parts_options else 0
                                        part_name = st.selectbox(f"Запчасть {i + 1}", parts_options,
                                                                 index=default_index if parts_options else 0,
                                                                 key=f"edit_part_name_{repair_id}_{i}")
                                    with col2:
                                        part_qty = st.number_input(f"Кол-во {i + 1}", 1, 100, value=default_qty,
                                                                   key=f"edit_part_qty_{repair_id}_{i}")
                                    with col3:
                                        keep = st.checkbox("Оставить", value=True, key=f"keep_part_{repair_id}_{i}")

                                    if keep and part_name:
                                        edited_parts.append((part_name, part_qty))

                                col1, col2 = st.columns(2)
                                with col1:
                                    if st.button("💾 Сохранить изменения", key=f"save_edit_{repair_id}",
                                                 use_container_width=True):
                                        updated_data = {
                                            'gos_number': new_gos_number,
                                            'repair_type': new_repair_type,
                                            'priority': new_priority,
                                            'employees': ", ".join(new_employees),
                                            'failure_reason': new_failure_reason,
                                            'tags': ", ".join(new_tags),
                                            'comment': new_comment,
                                            'works': ", ".join(edited_works),
                                            'parts': self.format_parts_string(edited_parts)
                                        }

                                        old_parts_dict = {name: qty for name, qty in current_parts}
                                        new_parts_dict = {name: qty for name, qty in edited_parts}

                                        for name, new_qty in new_parts_dict.items():
                                            old_qty = old_parts_dict.get(name, 0)
                                            if new_qty > old_qty:
                                                part_idx = st.session_state.spare_parts[
                                                    st.session_state.spare_parts['name'] == name
                                                    ].index
                                                if len(part_idx) > 0:
                                                    st.session_state.spare_parts.loc[part_idx[0], 'stock'] -= (
                                                            new_qty - old_qty)
                                            elif new_qty < old_qty:
                                                part_idx = st.session_state.spare_parts[
                                                    st.session_state.spare_parts['name'] == name
                                                    ].index
                                                if len(part_idx) > 0:
                                                    st.session_state.spare_parts.loc[part_idx[0], 'stock'] += (
                                                            old_qty - new_qty)

                                        for name, old_qty in old_parts_dict.items():
                                            if name not in new_parts_dict:
                                                part_idx = st.session_state.spare_parts[
                                                    st.session_state.spare_parts['name'] == name
                                                    ].index
                                                if len(part_idx) > 0:
                                                    st.session_state.spare_parts.loc[part_idx[0], 'stock'] += old_qty

                                        if self.update_repair(repair_id, updated_data):
                                            st.success("Изменения сохранены!")
                                            st.session_state[f"edit_{repair_id}"] = False
                                            st.rerun()

                                with col2:
                                    if st.button("❌ Отмена", key=f"cancel_edit_{repair_id}", use_container_width=True):
                                        st.session_state[f"edit_{repair_id}"] = False
                                        st.rerun()
                else:
                    st.info("Нет активных ремонтов")
            else:
                st.info("Нет данных о ремонтах")

        with tab3:
            st.subheader("📜 История завершенных ремонтов")

            search_gos = st.text_input("🔍 Фильтр по госномеру", placeholder="Введите номер...")

            if len(st.session_state.repairs) > 0:
                completed = st.session_state.repairs[
                    st.session_state.repairs['status'] == 'Завершен'
                    ].copy()

                if search_gos:
                    completed = completed[completed['gos_number'].str.contains(search_gos, case=False, na=False)]

                if len(completed) > 0:
                    for idx, repair in completed.iterrows():
                        with st.expander(f"✅ {repair['gos_number']} - завершен {repair['date_completion']}"):
                            col1, col2 = st.columns(2)
                            col1.write(f"**Тип:** {repair['repair_type']}")
                            col1.write(f"**Принят:** {repair['date_receipt']}")
                            col2.write(f"**Завершен:** {repair['date_completion']}")
                            col2.write(f"**Исполнители:** {repair['employees']}")

                            if repair['works']:
                                st.write(f"**🔧 Выполненные работы:** {repair['works']}")
                            if repair['parts']:
                                st.write(f"**🔩 Запчасти:** {repair['parts']}")

                            if st.button(f"🗑️ Удалить ремонт", key=f"history_delete_{repair['id']}"):
                                if self.delete_repair(repair['id']):
                                    st.success("Ремонт удален из истории!")
                                    st.rerun()
                else:
                    st.info("Нет завершенных ремонтов по указанному фильтру")
            else:
                st.info("Нет данных о ремонтах")

    def show_employees(self):
        """Управление сотрудниками"""
        st.header("👥 Управление сотрудниками")

        tab1, tab2, tab3 = st.tabs(["📋 Список сотрудников", "➕ Добавить", "✏️ Редактировать"])

        with tab1:
            if len(st.session_state.employees) > 0:
                display_df = st.session_state.employees.copy()
                display_df['daily_rate'] = display_df['daily_rate'].apply(lambda x: f"{x:,} ₽")
                st.dataframe(display_df, use_container_width=True)

                if st.button("📥 Экспорт списка сотрудников", key="export_employees"):
                    excel_data = self.export_manager.export_to_excel(
                        st.session_state.employees, "employees.xlsx", "Сотрудники"
                    )
                    st.download_button(
                        label="📥 Скачать Excel",
                        data=excel_data,
                        file_name="employees.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
            else:
                st.info("Нет данных о сотрудниках")

        with tab2:
            st.subheader("➕ Добавление нового сотрудника")
            col1, col2, col3 = st.columns(3)
            with col1:
                new_name = st.text_input("ФИО сотрудника", key="new_name")
            with col2:
                new_role = st.selectbox("Должность", ["Механик", "Механик-электрик"], key="new_role")
            with col3:
                new_rate = st.number_input("Ставка (день)", 3000, 15000, 5000, 500, key="new_rate")

            if st.button("➕ Добавить сотрудника", use_container_width=True):
                if new_name:
                    if self.add_employee(new_name, new_role, new_rate):
                        st.success(f"✅ Сотрудник {new_name} добавлен!")
                        st.rerun()
                    else:
                        st.error("Ошибка при добавлении!")
                else:
                    st.error("Введите ФИО сотрудника!")

        with tab3:
            st.subheader("✏️ Редактирование сотрудника")
            if len(st.session_state.employees) > 0:
                employees_list = st.session_state.employees['name'].tolist()
                selected_employee = st.selectbox("Выберите сотрудника", employees_list, key="edit_select")

                if selected_employee:
                    emp_data = st.session_state.employees[
                        st.session_state.employees['name'] == selected_employee
                        ].iloc[0]

                    col1, col2, col3 = st.columns(3)
                    with col1:
                        edit_name = st.text_input("ФИО", value=emp_data['name'], key="edit_name")
                    with col2:
                        edit_role = st.selectbox("Должность",
                                                 ["Механик", "Механик-электрик"],
                                                 index=0 if emp_data['role'] == "Механик" else 1,
                                                 key="edit_role")
                    with col3:
                        edit_rate = st.number_input("Ставка (день)",
                                                    value=int(emp_data['daily_rate']),
                                                    step=500, key="edit_rate")

                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("💾 Сохранить изменения", use_container_width=True):
                            if self.update_employee(selected_employee, edit_name, edit_role, edit_rate):
                                st.success("✅ Данные обновлены!")
                                st.rerun()
                            else:
                                st.error("Ошибка обновления!")

                    with col2:
                        if st.button("🗑️ Удалить сотрудника", use_container_width=True):
                            if self.delete_employee(selected_employee):
                                st.success(f"✅ Сотрудник {selected_employee} удален!")
                                st.rerun()
                            else:
                                st.error("Ошибка удаления!")
            else:
                st.info("Нет сотрудников для редактирования")

    def show_warehouse(self):
        """Управление складом с пополнением запасов"""
        st.header("📦 Управление складом")

        # 4 вкладки вместо 3
        tab1, tab2, tab3, tab4 = st.tabs(
            ["📋 Текущие остатки", "📊 Прогноз закупок", "➕ Добавить запчасть", "📥 Пополнение запасов"])

        with tab1:
            st.subheader("📋 Текущие остатки")

            search = st.text_input("🔍 Поиск запчастей", placeholder="Введите название...")

            df = st.session_state.spare_parts.copy()
            if search:
                df = df[df['name'].str.contains(search, case=False, na=False)]

            df['status'] = df.apply(
                lambda x: "🔴 Критический" if x['stock'] <= x['order_point']
                else "🟡 Норма" if x['stock'] <= x['min_stock'] * 1.5
                else "🟢 Достаточно", axis=1
            )

            st.dataframe(df, use_container_width=True)

            # Способ 5: Быстрое редактирование остатков
            st.markdown("---")
            st.subheader("✏️ Быстрое редактирование остатков")

            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                edit_part = st.selectbox("Выберите запчасть", df['name'].tolist(), key="edit_part_select")
            with col2:
                new_stock = st.number_input("Новый остаток", min_value=0, value=0, key="new_stock_value")
            with col3:
                if st.button("💾 Обновить остаток", key="update_stock_btn"):
                    if edit_part:
                        idx = st.session_state.spare_parts[st.session_state.spare_parts['name'] == edit_part].index[0]
                        old_stock = st.session_state.spare_parts.loc[idx, 'stock']
                        st.session_state.spare_parts.loc[idx, 'stock'] = new_stock
                        self.save_all()
                        st.success(f"✅ Остаток '{edit_part}' изменен: {old_stock} → {new_stock}")
                        st.rerun()

        with tab2:
            st.subheader("📊 Прогноз закупок запчастей")
            st.info("Прогноз основан на реальной статистике использования запчастей в ремонтах")

            col1, col2 = st.columns(2)
            with col1:
                st.subheader("📈 На 200 ремонтов")
                forecast_200 = self.get_parts_forecast(200)
                if len(forecast_200) > 0:
                    fig_frequency = px.bar(
                        forecast_200.head(10),
                        x='Запчасть',
                        y='Процент использования',
                        title='Частота использования запчастей (%)',
                        text='Процент использования',
                        color='Процент использования'
                    )
                    fig_frequency.update_traces(textposition='outside')
                    st.plotly_chart(fig_frequency, use_container_width=True)
                    st.dataframe(forecast_200, use_container_width=True)
                else:
                    st.info("Нет данных для прогноза (добавьте завершенные ремонты)")

            with col2:
                st.subheader("📅 На месяц")
                monthly_forecast = self.get_monthly_forecast()
                if len(monthly_forecast) > 0:
                    fig_monthly = px.bar(
                        monthly_forecast.head(10),
                        x='Запчасть',
                        y='Рекомендуемая закупка',
                        title='Рекомендуемая закупка на месяц',
                        text='Рекомендуемая закупка',
                        color='Рекомендуемая закупка'
                    )
                    fig_monthly.update_traces(textposition='outside')
                    st.plotly_chart(fig_monthly, use_container_width=True)
                    st.dataframe(monthly_forecast, use_container_width=True)
                else:
                    st.info("Нет данных для прогноза (добавьте завершенные ремонты)")

        with tab3:
            st.subheader("➕ Добавление новой запчасти")
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                new_name = st.text_input("Название", key="new_part_name")
            with col2:
                new_stock = st.number_input("Остаток", 0, 1000, 10, key="new_part_stock")
            with col3:
                new_min = st.number_input("Мин. запас", 0, 100, 5, key="new_part_min")
            with col4:
                new_order = st.number_input("Точка заказа", 0, 100, 8, key="new_part_order")

            if st.button("➕ Добавить запчасть", key="add_part_btn"):
                if new_name:
                    new_row = pd.DataFrame([{
                        'name': new_name, 'stock': new_stock,
                        'min_stock': new_min, 'order_point': new_order
                    }])
                    st.session_state.spare_parts = pd.concat([st.session_state.spare_parts, new_row], ignore_index=True)
                    self.save_all()
                    st.success(f"✅ Запчасть '{new_name}' добавлена")
                    st.rerun()

        with tab4:
            # Способ 3: Ручное пополнение запасов
            st.subheader("📥 Пополнение запасов")
            st.info("Добавьте новые поступления запчастей на склад")

            # Выбор запчасти
            parts_list = st.session_state.spare_parts['name'].tolist()
            selected_part = st.selectbox("Выберите запчасть для пополнения", parts_list, key="restock_part")

            if selected_part:
                # Получаем текущую информацию
                part_idx = st.session_state.spare_parts[st.session_state.spare_parts['name'] == selected_part].index[0]
                current_stock = st.session_state.spare_parts.loc[part_idx, 'stock']

                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Текущий остаток", f"{current_stock} шт.")
                with col2:
                    min_stock = st.session_state.spare_parts.loc[part_idx, 'min_stock']
                    st.metric("Мин. запас", f"{min_stock} шт.")
                with col3:
                    order_point = st.session_state.spare_parts.loc[part_idx, 'order_point']
                    st.metric("Точка заказа", f"{order_point} шт.")

                st.markdown("---")

                # Форма для добавления
                col1, col2 = st.columns(2)
                with col1:
                    add_quantity = st.number_input(
                        "Количество для добавления",
                        min_value=1,
                        max_value=1000,
                        value=10,
                        step=5,
                        key="add_quantity"
                    )

                with col2:
                    supplier = st.text_input("Поставщик (опционально)", placeholder="Название компании", key="supplier")

                # Дополнительная информация
                invoice_number = st.text_input("Номер накладной (опционально)", placeholder="№123456", key="invoice")
                comment = st.text_area("Комментарий к поступлению",
                                       placeholder="Например: новая партия, брак, возврат и т.д.",
                                       key="restock_comment")

                st.markdown("---")

                col1, col2 = st.columns(2)
                with col1:
                    if st.button("✅ Подтвердить поступление", use_container_width=True, key="confirm_restock"):
                        # Обновляем остаток
                        new_stock = current_stock + add_quantity
                        st.session_state.spare_parts.loc[part_idx, 'stock'] = new_stock

                        # Сохраняем изменения
                        self.save_all()

                        # Показываем успех
                        st.success(f"✅ На склад добавлено {add_quantity} шт. '{selected_part}'")
                        st.info(f"📊 Новый остаток: {new_stock} шт. (было: {current_stock})")

                        if supplier:
                            st.info(f"📦 Поставщик: {supplier}")
                        if invoice_number:
                            st.info(f"📄 Накладная: {invoice_number}")
                        if comment:
                            st.info(f"💬 {comment}")

                        st.balloons()
                        time.sleep(2)
                        st.rerun()

                with col2:
                    if st.button("❌ Отмена", use_container_width=True, key="cancel_restock"):
                        st.rerun()

            st.markdown("---")

            # Способ 4: Массовый импорт из Excel
            with st.expander("📊 Массовый импорт из Excel"):
                st.info("Загрузите Excel файл с колонками: name, stock, min_stock, order_point")
                st.warning(
                    "⚠️ Внимание: Если запчасть с таким названием уже существует, её остаток будет УВЕЛИЧЕН на указанное значение")

                # Шаблон для скачивания
                template_df = pd.DataFrame({
                    'name': ['Новая запчасть 1', 'Новая запчасть 2'],
                    'stock': [10, 20],
                    'min_stock': [5, 10],
                    'order_point': [8, 15]
                })

                # Сохраняем шаблон в BytesIO
                template_buffer = BytesIO()
                with pd.ExcelWriter(template_buffer, engine='openpyxl') as writer:
                    template_df.to_excel(writer, sheet_name='Запчасти', index=False)
                template_buffer.seek(0)

                st.download_button(
                    label="📥 Скачать шаблон Excel",
                    data=template_buffer.getvalue(),
                    file_name="template_parts.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key="download_template"
                )

                uploaded_file = st.file_uploader("Загрузите Excel файл", type=['xlsx', 'xls'], key="bulk_upload")

                if uploaded_file:
                    try:
                        # Читаем Excel
                        df_bulk = pd.read_excel(uploaded_file)

                        # Проверяем колонки
                        required_columns = ['name', 'stock', 'min_stock', 'order_point']
                        missing_columns = [col for col in required_columns if col not in df_bulk.columns]

                        if missing_columns:
                            st.error(f"❌ Отсутствуют колонки: {missing_columns}")
                        else:
                            # Показываем предпросмотр
                            st.subheader("📋 Предпросмотр данных:")
                            st.dataframe(df_bulk.head(10), use_container_width=True)

                            # Подтверждение
                            if st.button("✅ Подтвердить массовый импорт", use_container_width=True, key="confirm_bulk"):
                                added_count = 0
                                updated_count = 0

                                for _, row in df_bulk.iterrows():
                                    name = row['name']
                                    stock_to_add = row.get('stock', 0)
                                    min_stock = row.get('min_stock', 10)
                                    order_point = row.get('order_point', 15)

                                    existing = st.session_state.spare_parts[
                                        st.session_state.spare_parts['name'] == name]

                                    if len(existing) > 0:
                                        # Обновляем существующую (увеличиваем остаток)
                                        idx = existing.index[0]
                                        old_stock = st.session_state.spare_parts.loc[idx, 'stock']
                                        st.session_state.spare_parts.loc[idx, 'stock'] = old_stock + stock_to_add
                                        updated_count += 1
                                    else:
                                        # Добавляем новую
                                        new_part = pd.DataFrame([{
                                            'name': name,
                                            'stock': stock_to_add,
                                            'min_stock': min_stock,
                                            'order_point': order_point
                                        }])
                                        st.session_state.spare_parts = pd.concat(
                                            [st.session_state.spare_parts, new_part], ignore_index=True)
                                        added_count += 1

                                self.save_all()
                                st.success(
                                    f"✅ Массовый импорт завершен! Добавлено: {added_count}, Обновлено: {updated_count}")
                                st.balloons()
                                time.sleep(2)
                                st.rerun()

                    except Exception as e:
                        st.error(f"❌ Ошибка при чтении файла: {e}")

        st.markdown("---")
        st.subheader("📤 Экспорт данных склада")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("📥 Экспорт склада в Excel", use_container_width=True):
                excel_data = self.export_manager.export_warehouse(st.session_state.spare_parts)
                st.download_button(
                    label="📥 Скачать Excel",
                    data=excel_data,
                    file_name=f"warehouse_{datetime.date.today()}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

        with col2:
            if st.button("📥 Экспорт в CSV", use_container_width=True):
                csv_data = self.export_manager.export_to_csv(st.session_state.spare_parts, "warehouse.csv")
                st.download_button(
                    label="📥 Скачать CSV",
                    data=csv_data,
                    file_name=f"warehouse_{datetime.date.today()}.csv",
                    mime="text/csv"
                )

    def show_analytics(self):
        """Аналитика с расширенной статистикой"""
        st.header("📈 Аналитика")

        # Выбор периода
        col1, col2, col3 = st.columns(3)
        with col1:
            analytics_type = st.selectbox(
                "Тип аналитики",
                ["По дням", "По месяцам", "По годам"],
                key="analytics_type"
            )
        with col2:
            year = st.number_input("Год", value=datetime.date.today().year, min_value=2024, key="analytics_year")
        with col3:
            if analytics_type == "По месяцам":
                month = st.selectbox("Месяц", range(1, 13), format_func=lambda x: f"{x:02d}", key="analytics_month")
            else:
                month = None

        # Получаем данные
        if len(st.session_state.repairs) > 0:
            repairs = st.session_state.repairs.copy()
            repairs['date_dt'] = pd.to_datetime(repairs['date_receipt'])

            # Фильтрация по периоду
            if analytics_type == "По дням":
                selected_date = st.date_input("Выберите дату", datetime.date.today(), key="analytics_date")
                period_repairs = repairs[repairs['date_dt'].dt.date == selected_date]
                period_label = selected_date.strftime('%d.%m.%Y')
            elif analytics_type == "По месяцам":
                period_repairs = repairs[
                    (repairs['date_dt'].dt.year == year) &
                    (repairs['date_dt'].dt.month == month)
                    ]
                period_label = f"{month:02d}.{year}"
            else:  # По годам
                period_repairs = repairs[repairs['date_dt'].dt.year == year]
                period_label = str(year)
        else:
            period_repairs = pd.DataFrame()
            period_label = "Нет данных"

        # Получаем данные о рабочих днях
        if len(st.session_state.work_days) > 0:
            work_days = st.session_state.work_days.copy()
            work_days['date_dt'] = pd.to_datetime(work_days['date'])

            if analytics_type == "По дням":
                selected_date = st.session_state.get('analytics_date', datetime.date.today())
                period_days = work_days[work_days['date_dt'].dt.date == selected_date]
            elif analytics_type == "По месяцам":
                period_days = work_days[
                    (work_days['date_dt'].dt.year == year) &
                    (work_days['date_dt'].dt.month == month)
                    ]
            else:
                period_days = work_days[work_days['date_dt'].dt.year == year]
        else:
            period_days = pd.DataFrame()

        # Вкладки для разных разделов
        tab1, tab2, tab3, tab4 = st.tabs(["📊 Дашборд", "📋 Ремонты", "🏆 KPI сотрудников", "📦 Аналитика склада"])

        with tab1:
            st.subheader(f"📊 Дашборд за {period_label}")

            col1, col2, col3, col4 = st.columns(4)
            with col1:
                total_repairs = len(period_repairs)
                st.metric("🔧 Всего ремонтов", total_repairs)
            with col2:
                completed = len(period_repairs[period_repairs['status'] == 'Завершен']) if len(
                    period_repairs) > 0 else 0
                st.metric("✅ Завершено", completed)
            with col3:
                in_progress = len(period_repairs[period_repairs['status'] == 'В работе']) if len(
                    period_repairs) > 0 else 0
                st.metric("🔄 В работе", in_progress)
            with col4:
                st.metric("👥 Сотрудников", len(st.session_state.employees))

            st.markdown("---")

            # Графики
            if len(period_repairs) > 0:
                col1, col2 = st.columns(2)
                with col1:
                    type_counts = period_repairs['repair_type'].value_counts()
                    if len(type_counts) > 0:
                        fig = px.pie(
                            values=type_counts.values,
                            names=type_counts.index,
                            title="Распределение по типам ремонта",
                            color_discrete_sequence=px.colors.qualitative.Set3
                        )
                        fig.update_traces(textposition='inside', textinfo='percent+label')
                        st.plotly_chart(fig, use_container_width=True)

                with col2:
                    priority_counts = period_repairs['priority'].value_counts()
                    if len(priority_counts) > 0:
                        colors = {'Высокий': '#ff6b6b', 'Средний': '#ffd93d', 'Низкий': '#6bcb77'}
                        fig = px.bar(
                            x=priority_counts.index,
                            y=priority_counts.values,
                            title="Приоритеты ремонтов",
                            color=priority_counts.index,
                            color_discrete_map=colors,
                            text=priority_counts.values
                        )
                        fig.update_traces(textposition='outside')
                        st.plotly_chart(fig, use_container_width=True)

                status_counts = period_repairs['status'].value_counts()
                if len(status_counts) > 0:
                    fig = px.bar(
                        x=status_counts.index,
                        y=status_counts.values,
                        title="Статусы ремонтов",
                        color=status_counts.index,
                        text=status_counts.values
                    )
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Нет данных для отображения")

        with tab2:
            st.subheader(f"📋 Статистика ремонтов за {period_label}")

            if len(period_repairs) > 0:
                col1, col2, col3 = st.columns(3)
                with col1:
                    if analytics_type == "По дням":
                        st.metric("📊 Ремонтов за день", len(period_repairs))
                    elif analytics_type == "По месяцам":
                        days_in_month = calendar.monthrange(year, month)[1]
                        avg_per_day = len(period_repairs) / days_in_month if days_in_month > 0 else 0
                        st.metric("📊 Ремонтов за месяц", len(period_repairs))
                        st.metric("📈 В среднем в день", f"{avg_per_day:.1f}")
                    else:
                        avg_per_month = len(period_repairs) / 12 if len(period_repairs) > 0 else 0
                        st.metric("📊 Ремонтов за год", len(period_repairs))
                        st.metric("📈 В среднем в месяц", f"{avg_per_month:.1f}")

                with col2:
                    in_repair = len(period_repairs[period_repairs['status'] == 'В работе'])
                    closed = len(period_repairs[period_repairs['status'] == 'Завершен'])
                    st.metric("🔄 В ремонте", in_repair)
                    st.metric("✅ Закрыто", closed)

                with col3:
                    completion_rate = (closed / len(period_repairs) * 100) if len(period_repairs) > 0 else 0
                    st.metric("📊 Процент завершения", f"{completion_rate:.1f}%")

                st.markdown("---")

                if analytics_type in ["По месяцам", "По годам"]:
                    st.subheader("📈 Динамика поступлений ремонтов")

                    if analytics_type == "По месяцам":
                        days_in_month = calendar.monthrange(year, month)[1]
                        daily_counts = []
                        for day in range(1, days_in_month + 1):
                            date_obj = datetime.date(year, month, day)
                            count = len(period_repairs[period_repairs['date_dt'].dt.date == date_obj])
                            daily_counts.append({'Дата': date_obj, 'Ремонтов': count})

                        daily_df = pd.DataFrame(daily_counts)
                        fig = px.bar(
                            daily_df,
                            x='Дата',
                            y='Ремонтов',
                            title=f"Поступление ремонтов за {month:02d}.{year}",
                            text='Ремонтов'
                        )
                        fig.update_traces(textposition='outside')
                        fig.update_layout(xaxis_title="Дата", yaxis_title="Количество ремонтов")
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        monthly_counts = []
                        for m in range(1, 13):
                            count = len(period_repairs[
                                            (period_repairs['date_dt'].dt.year == year) &
                                            (period_repairs['date_dt'].dt.month == m)
                                            ])
                            monthly_counts.append({'Месяц': f"{m:02d}", 'Ремонтов': count})

                        monthly_df = pd.DataFrame(monthly_counts)
                        fig = px.bar(
                            monthly_df,
                            x='Месяц',
                            y='Ремонтов',
                            title=f"Поступление ремонтов за {year} год",
                            text='Ремонтов'
                        )
                        fig.update_traces(textposition='outside')
                        fig.update_layout(xaxis_title="Месяц", yaxis_title="Количество ремонтов")
                        st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Нет данных для отображения")

        with tab3:
            st.subheader(f"🏆 KPI сотрудников за {period_label}")

            if len(st.session_state.employees) > 0:
                total_repairs = len(period_repairs)
                total_employees = len(st.session_state.employees)
                avg_per_employee = total_repairs / total_employees if total_employees > 0 else 0

                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("👥 Всего сотрудников", total_employees)
                with col2:
                    st.metric("🔧 Всего ремонтов", total_repairs)
                with col3:
                    st.metric("📊 В среднем на сотрудника", f"{avg_per_employee:.1f}")

                st.markdown("---")

                kpi_data = []
                for _, emp in st.session_state.employees.iterrows():
                    emp_repairs = period_repairs[
                        period_repairs['employees'].str.contains(emp['name'], na=False)] if len(
                        period_repairs) > 0 else pd.DataFrame()
                    repairs_count = len(emp_repairs)
                    completed_count = len(emp_repairs[emp_repairs['status'] == 'Завершен']) if len(
                        emp_repairs) > 0 else 0

                    emp_days = period_days[period_days['employee'] == emp['name']] if len(
                        period_days) > 0 else pd.DataFrame()
                    days_worked = len(emp_days)

                    productivity = repairs_count / days_worked if days_worked > 0 else 0

                    kpi_data.append({
                        'Сотрудник': emp['name'],
                        'Роль': emp['role'],
                        'Ремонтов': repairs_count,
                        'Завершено': completed_count,
                        'Отработано дней': days_worked,
                        'Производительность': f"{productivity:.2f} рем/день"
                    })

                kpi_df = pd.DataFrame(kpi_data).sort_values('Ремонтов', ascending=False)
                st.dataframe(kpi_df, use_container_width=True)

                st.markdown("---")
                st.subheader("📊 Визуализация KPI")

                col1, col2 = st.columns(2)
                with col1:
                    fig1 = px.bar(
                        kpi_df,
                        x='Сотрудник',
                        y='Ремонтов',
                        title='Количество ремонтов по сотрудникам',
                        color='Ремонтов',
                        text='Ремонтов'
                    )
                    fig1.update_traces(textposition='outside')
                    st.plotly_chart(fig1, use_container_width=True)

                with col2:
                    fig2 = px.bar(
                        kpi_df,
                        x='Сотрудник',
                        y='Отработано дней',
                        title='Отработанные дни по сотрудникам',
                        color='Отработано дней',
                        text='Отработано дней'
                    )
                    fig2.update_traces(textposition='outside')
                    st.plotly_chart(fig2, use_container_width=True)

                fig3 = px.bar(
                    kpi_df,
                    x='Сотрудник',
                    y='Производительность',
                    title='Производительность (ремонтов в день)',
                    color='Производительность',
                    text='Производительность'
                )
                fig3.update_traces(textposition='outside')
                st.plotly_chart(fig3, use_container_width=True)

            else:
                st.info("Нет данных о сотрудниках")

        with tab4:
            st.subheader("📦 Аналитика склада")

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("📦 Всего запчастей", len(st.session_state.spare_parts))
            with col2:
                total_stock = st.session_state.spare_parts['stock'].sum() if len(
                    st.session_state.spare_parts) > 0 else 0
                st.metric("📊 Общий остаток", f"{total_stock} шт.")
            with col3:
                deficit_count = len(st.session_state.spare_parts[
                                        st.session_state.spare_parts['stock'] <= st.session_state.spare_parts[
                                            'order_point']
                                        ])
                st.metric("⚠️ Дефицит", deficit_count)

            st.markdown("---")

            low_stock = st.session_state.spare_parts[
                st.session_state.spare_parts['stock'] <= st.session_state.spare_parts['order_point']
                ]
            if len(low_stock) > 0:
                st.warning(f"⚠️ Внимание! {len(low_stock)} запчастей требуют пополнения:")
                st.dataframe(low_stock[['name', 'stock', 'min_stock', 'order_point']], use_container_width=True)
            else:
                st.success("✅ Все запчасти в достаточном количестве")

            st.markdown("---")
            st.subheader("📊 Прогноз закупок")

            st.info("Прогноз основан на реальной статистике использования запчастей в ремонтах")

            col1, col2 = st.columns(2)
            with col1:
                st.markdown("### 📈 На 200 ремонтов")
                forecast_200 = self.get_parts_forecast(200)
                if len(forecast_200) > 0:
                    fig_freq = px.bar(
                        forecast_200.head(10),
                        x='Запчасть',
                        y='Процент использования',
                        title='Частота использования запчастей (%)',
                        text='Процент использования',
                        color='Процент использования'
                    )
                    fig_freq.update_traces(textposition='outside')
                    st.plotly_chart(fig_freq, use_container_width=True)

                    fig = px.bar(
                        forecast_200.head(10),
                        x='Запчасть',
                        y='Рекомендуемая закупка',
                        title='Рекомендуемая закупка на 200 ремонтов',
                        text='Рекомендуемая закупка',
                        color='Рекомендуемая закупка'
                    )
                    fig.update_traces(textposition='outside')
                    st.plotly_chart(fig, use_container_width=True)
                    st.dataframe(forecast_200, use_container_width=True)
                else:
                    st.info("Нет данных для прогноза (добавьте завершенные ремонты)")

            with col2:
                st.markdown("### 📅 На месяц")
                monthly_forecast = self.get_monthly_forecast()
                if len(monthly_forecast) > 0:
                    fig = px.bar(
                        monthly_forecast.head(10),
                        x='Запчасть',
                        y='Рекомендуемая закупка',
                        title='Рекомендуемая закупка на месяц',
                        text='Рекомендуемая закупка',
                        color='Рекомендуемая закупка'
                    )
                    fig.update_traces(textposition='outside')
                    st.plotly_chart(fig, use_container_width=True)
                    st.dataframe(monthly_forecast, use_container_width=True)
                else:
                    st.info("Нет данных для прогноза (добавьте завершенные ремонты)")

            st.markdown("---")
            st.subheader("📤 Экспорт аналитики")

            if st.button("📥 Экспорт аналитики в Excel", use_container_width=True):
                excel_data = self.export_manager.export_analytics(
                    period_repairs, st.session_state.spare_parts,
                    st.session_state.employees, period_label
                )
                st.download_button(
                    label="📥 Скачать Excel",
                    data=excel_data,
                    file_name=f"analytics_{period_label}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

    def show_reports(self):
        """Отчеты с KPI сотрудников, аналитикой по складу и дашбордом"""
        st.header("📑 Комплексный отчет")

        col1, col2 = st.columns(2)
        with col1:
            report_month = st.selectbox("Месяц", range(1, 13), format_func=lambda x: f"{x:02d}", key="report_month")
        with col2:
            report_year = st.number_input("Год", value=datetime.date.today().year, key="report_year")

        if len(st.session_state.repairs) > 0:
            repairs = st.session_state.repairs.copy()
            repairs['date_dt'] = pd.to_datetime(repairs['date_receipt'])
            period_repairs = repairs[
                (repairs['date_dt'].dt.year == report_year) &
                (repairs['date_dt'].dt.month == report_month)
                ].copy()

            if len(st.session_state.work_days) > 0:
                work_days = st.session_state.work_days.copy()
                work_days['date_dt'] = pd.to_datetime(work_days['date'])
                period_days = work_days[
                    (work_days['date_dt'].dt.year == report_year) &
                    (work_days['date_dt'].dt.month == report_month)
                    ]
            else:
                period_days = pd.DataFrame()

            report_tab1, report_tab2, report_tab3, report_tab4 = st.tabs(
                ["📊 Дашборд", "📋 Ремонты", "🏆 KPI сотрудников", "📦 Аналитика склада"]
            )

            with report_tab1:
                st.subheader(f"📊 Сводка за {report_month:02d}.{report_year}")

                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("🔧 Всего ремонтов", len(period_repairs))
                with col2:
                    completed = len(period_repairs[period_repairs['status'] == 'Завершен'])
                    st.metric("✅ Завершено", completed)
                with col3:
                    st.metric("👥 Сотрудников", len(st.session_state.employees))
                with col4:
                    deficit = len(st.session_state.spare_parts[
                                      st.session_state.spare_parts['stock'] <= st.session_state.spare_parts[
                                          'order_point']
                                      ])
                    st.metric("📦 Дефицит запчастей", deficit)

                st.markdown("---")

                if len(period_repairs) > 0:
                    completed_repairs = period_repairs[period_repairs['status'] == 'Завершен']
                    avg_time = 0
                    if len(completed_repairs) > 0:
                        times = []
                        for _, repair in completed_repairs.iterrows():
                            if repair['date_completion']:
                                start = datetime.datetime.strptime(repair['date_receipt'], '%Y-%m-%d')
                                end = datetime.datetime.strptime(repair['date_completion'], '%Y-%m-%d')
                                times.append((end - start).days)
                        avg_time = sum(times) / len(times) if times else 0

                    urgent_pct = (len(period_repairs[period_repairs['priority'] == 'Высокий']) / len(
                        period_repairs)) * 100

                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("⏱️ Среднее время ремонта", f"{avg_time:.1f} дн.")
                    with col2:
                        st.metric("🚨 Срочных ремонтов", f"{urgent_pct:.0f}%")

            with report_tab2:
                st.subheader("📋 Детальный список ремонтов")

                if len(period_repairs) > 0:
                    report_data = []
                    for _, repair in period_repairs.iterrows():
                        duration = ""
                        if repair['date_completion']:
                            start = datetime.datetime.strptime(repair['date_receipt'], '%Y-%m-%d')
                            end = datetime.datetime.strptime(repair['date_completion'], '%Y-%m-%d')
                            duration = f"{(end - start).days} дн."
                        else:
                            duration = "В работе"

                        report_data.append({
                            'ID': repair['id'],
                            'Госномер': repair['gos_number'],
                            'Дата приема': repair['date_receipt'],
                            'Дата завершения': repair['date_completion'] if repair['date_completion'] else '—',
                            'Длительность': duration,
                            'Тип ремонта': repair['repair_type'],
                            'Причина': repair['failure_reason'],
                            'Приоритет': repair['priority'],
                            'Статус': repair['status'],
                            'Исполнители': repair['employees'],
                            'Работы': repair['works'] if repair['works'] else '—',
                            'Запчасти': repair['parts'] if repair['parts'] else '—',
                            'Комментарий': repair['comment'] if repair['comment'] else '—'
                        })

                    st.dataframe(pd.DataFrame(report_data), use_container_width=True)
                else:
                    st.info("Нет ремонтов за выбранный период")

            with report_tab3:
                st.subheader("🏆 KPI сотрудников")

                if len(st.session_state.employees) > 0:
                    kpi_data = []
                    for _, emp in st.session_state.employees.iterrows():
                        emp_repairs = period_repairs[
                            period_repairs['employees'].str.contains(emp['name'], na=False)] if len(
                            period_repairs) > 0 else pd.DataFrame()
                        repairs_count = len(emp_repairs)
                        completed_count = len(emp_repairs[emp_repairs['status'] == 'Завершен']) if len(
                            emp_repairs) > 0 else 0

                        emp_days = period_days[period_days['employee'] == emp['name']] if len(
                            period_days) > 0 else pd.DataFrame()
                        days_worked = len(emp_days)

                        fot = days_worked * emp['daily_rate']
                        productivity = repairs_count / days_worked if days_worked > 0 else 0

                        kpi_data.append({
                            'Сотрудник': emp['name'],
                            'Роль': emp['role'],
                            'Ремонтов': repairs_count,
                            'Завершено': completed_count,
                            'Отработано дней': days_worked,
                            'Производительность': f"{productivity:.2f} рем/день",
                            'ФОТ, ₽': fot
                        })

                    kpi_df = pd.DataFrame(kpi_data).sort_values('Ремонтов', ascending=False)
                    st.dataframe(kpi_df, use_container_width=True)

                    col1, col2 = st.columns(2)
                    with col1:
                        fig1 = px.bar(kpi_df, x='Сотрудник', y='Ремонтов', title='Ремонты по сотрудникам',
                                      color='Ремонтов', text='Ремонтов')
                        st.plotly_chart(fig1, use_container_width=True)
                    with col2:
                        fig2 = px.bar(kpi_df, x='Сотрудник', y='Отработано дней', title='Отработанные дни',
                                      color='Отработано дней', text='Отработано дней')
                        st.plotly_chart(fig2, use_container_width=True)
                else:
                    st.info("Нет данных о сотрудниках")

            with report_tab4:
                st.subheader("📦 Аналитика склада")

                col1, col2 = st.columns(2)
                with col1:
                    st.metric("📦 Всего запчастей", len(st.session_state.spare_parts))
                    deficit_count = len(st.session_state.spare_parts[
                                            st.session_state.spare_parts['stock'] <= st.session_state.spare_parts[
                                                'order_point']
                                            ])
                    st.metric("⚠️ Дефицит", deficit_count)

                with col2:
                    total_stock = st.session_state.spare_parts['stock'].sum() if len(
                        st.session_state.spare_parts) > 0 else 0
                    st.metric("📊 Общий остаток", f"{total_stock} шт.")

                st.markdown("---")

                low_stock = st.session_state.spare_parts[
                    st.session_state.spare_parts['stock'] <= st.session_state.spare_parts['order_point']
                    ]
                if len(low_stock) > 0:
                    st.warning("⚠️ Запчасти, требующие пополнения:")
                    st.dataframe(low_stock[['name', 'stock', 'order_point']], use_container_width=True)
                else:
                    st.success("✅ Все запчасти в достаточном количестве")

                st.markdown("---")
                st.subheader("📊 Прогнозы закупок")

                forecast_200 = self.get_parts_forecast(200)
                if len(forecast_200) > 0:
                    st.caption("Прогноз на 200 ремонтов")
                    st.dataframe(forecast_200.head(10), use_container_width=True)

            st.markdown("---")
            if st.button("📥 Экспорт полного отчета в Excel", use_container_width=True):
                output = BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    dashboard_data = pd.DataFrame([{
                        'Месяц': f"{report_month:02d}.{report_year}",
                        'Всего ремонтов': len(period_repairs),
                        'Завершено': len(period_repairs[period_repairs['status'] == 'Завершен']),
                        'Сотрудников': len(st.session_state.employees),
                        'Дефицит запчастей': len(st.session_state.spare_parts[
                                                     st.session_state.spare_parts['stock'] <=
                                                     st.session_state.spare_parts['order_point']
                                                     ])
                    }])
                    dashboard_data.to_excel(writer, sheet_name='Дашборд', index=False)

                    if len(period_repairs) > 0:
                        period_repairs.to_excel(writer, sheet_name='Ремонты', index=False)

                    if len(st.session_state.employees) > 0:
                        kpi_data = []
                        for _, emp in st.session_state.employees.iterrows():
                            emp_repairs = period_repairs[
                                period_repairs['employees'].str.contains(emp['name'], na=False)] if len(
                                period_repairs) > 0 else pd.DataFrame()
                            emp_days = period_days[period_days['employee'] == emp['name']] if len(
                                period_days) > 0 else pd.DataFrame()
                            kpi_data.append({
                                'Сотрудник': emp['name'],
                                'Роль': emp['role'],
                                'Ремонтов': len(emp_repairs),
                                'Завершено': len(emp_repairs[emp_repairs['status'] == 'Завершен']),
                                'Отработано дней': len(emp_days),
                                'ФОТ': len(emp_days) * emp['daily_rate']
                            })
                        pd.DataFrame(kpi_data).to_excel(writer, sheet_name='KPI', index=False)

                    st.session_state.spare_parts.to_excel(writer, sheet_name='Склад', index=False)

                    forecast_200 = self.get_parts_forecast(200)
                    if len(forecast_200) > 0:
                        forecast_200.to_excel(writer, sheet_name='Прогноз_200', index=False)

                st.download_button(
                    label="📥 Скачать Excel",
                    data=output.getvalue(),
                    file_name=f"full_report_{report_year}_{report_month:02d}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
        else:
            st.info("Нет данных для формирования отчета")

    def show_work_days(self):
        """Учет отработанных дней с календарем"""
        st.header("📅 Учет отработанных дней")

        st.subheader("🚀 Быстрая отметка")

        col1, col2, col3 = st.columns([2, 2, 1])
        with col1:
            selected_employee = st.selectbox("Сотрудник", st.session_state.employees['name'].tolist(),
                                             key="quick_employee")
        with col2:
            work_date = st.date_input("Дата", datetime.date.today(), key="quick_date")
        with col3:
            st.write("")
            st.write("")
            if st.button("✅ Вышел на смену", key="check_in_btn", use_container_width=True):
                success, message = self.add_work_day(work_date, selected_employee, 8, "")
                if success:
                    st.success(f"✅ {selected_employee} отметил начало смены {work_date}")
                    st.rerun()
                else:
                    st.error(message)

        st.markdown("---")

        st.subheader("📅 Календарь отработанных дней")

        col1, col2 = st.columns([3, 1])
        with col1:
            calendar_month = st.selectbox("Месяц", range(1, 13), format_func=lambda x: f"{x:02d}", key="cal_month")
            calendar_year = st.number_input("Год", value=datetime.date.today().year, min_value=2024, key="cal_year")
        with col2:
            st.write("")
            st.write("")
            st.markdown("**Легенда:**")
            st.markdown("🟢 **Зеленый** - есть работавшие")
            st.markdown("🔴 **Красный** - нет работавших")

        start_date = datetime.date(calendar_year, calendar_month, 1)
        if calendar_month == 12:
            end_date = datetime.date(calendar_year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = datetime.date(calendar_year, calendar_month + 1, 1) - timedelta(days=1)

        cal = calendar.monthcalendar(calendar_year, calendar_month)

        work_by_date = {}
        if len(st.session_state.work_days) > 0:
            for _, day in st.session_state.work_days.iterrows():
                if start_date <= datetime.datetime.strptime(day['date'], '%Y-%m-%d').date() <= end_date:
                    date_str = day['date']
                    if date_str not in work_by_date:
                        work_by_date[date_str] = []
                    work_by_date[date_str].append(day['employee'])

        st.markdown("---")

        days = ['ПН', 'ВТ', 'СР', 'ЧТ', 'ПТ', 'СБ', 'ВС']
        cols = st.columns(7)
        for i, day in enumerate(days):
            cols[i].markdown(f"**{day}**")

        for week in cal:
            cols = st.columns(7)
            for i, day in enumerate(week):
                if day == 0:
                    cols[i].markdown('<div class="calendar-day-empty"></div>', unsafe_allow_html=True)
                else:
                    current_date = datetime.date(calendar_year, calendar_month, day)
                    date_str = current_date.isoformat()

                    if date_str in work_by_date:
                        employees_list = ", ".join(work_by_date[date_str])
                        cols[i].markdown(
                            f'<div class="calendar-day-work" title="Работали: {employees_list}">'
                            f'<b>{day}</b><br>'
                            f'<span style="font-size: 11px;">👥 {len(work_by_date[date_str])}</span>'
                            f'</div>',
                            unsafe_allow_html=True
                        )
                    else:
                        cols[i].markdown(
                            f'<div class="calendar-day-off" title="Нет работавших">'
                            f'<b>{day}</b><br>'
                            f'<span style="font-size: 11px;">❌</span>'
                            f'</div>',
                            unsafe_allow_html=True
                        )

        st.markdown("---")

        st.subheader("📋 Детальная информация по дню")

        selected_date = st.date_input("Выберите дату для просмотра", datetime.date.today(), key="detail_date")
        date_str = selected_date.isoformat()

        if date_str in work_by_date:
            st.success(f"✅ {selected_date.strftime('%d.%m.%Y')} - работали следующие сотрудники:")
            for emp in work_by_date[date_str]:
                emp_data = st.session_state.employees[st.session_state.employees['name'] == emp]
                if len(emp_data) > 0:
                    st.write(f"• {emp} ({emp_data.iloc[0]['role']})")

            day_records = st.session_state.work_days[st.session_state.work_days['date'] == date_str]
            if len(day_records) > 0:
                st.write("**Детали:**")
                for _, record in day_records.iterrows():
                    st.write(
                        f"  - {record['employee']}: {record['hours_worked']} ч., ремонты: {record['repair_ids'] if record['repair_ids'] else '—'}")
        else:
            st.info(f"ℹ️ {selected_date.strftime('%d.%m.%Y')} - никто не работал")

        st.markdown("---")

        with st.expander("📋 Полный список отработанных дней"):
            if len(st.session_state.work_days) > 0:
                filtered_days = st.session_state.work_days.copy()
                filtered_days = filtered_days.sort_values('date', ascending=False)

                for idx, day in filtered_days.iterrows():
                    st.write(f"**{day['date']}** - {day['employee']} - {day['hours_worked']} ч.")
                    if day['repair_ids']:
                        st.write(f"  Ремонты: {day['repair_ids']}")
                    if st.button(f"🗑️ Удалить", key=f"delete_day_{idx}"):
                        if self.delete_work_day(idx):
                            st.success("Запись удалена!")
                            st.rerun()
                    st.markdown("---")
            else:
                st.info("Нет данных об отработанных днях")

    def show_employee_kpi(self):
        """KPI сотрудников"""
        st.header("🏆 KPI сотрудников")

        if len(st.session_state.employees) > 0:
            col1, col2 = st.columns(2)
            with col1:
                kpi_month = st.selectbox("Месяц", range(1, 13), format_func=lambda x: f"{x:02d}", key="kpi_month")
            with col2:
                kpi_year = st.number_input("Год", value=datetime.date.today().year, min_value=2024, key="kpi_year")

            if len(st.session_state.repairs) > 0:
                repairs = st.session_state.repairs.copy()
                repairs['date_dt'] = pd.to_datetime(repairs['date_receipt'])
                period_repairs = repairs[
                    (repairs['date_dt'].dt.year == kpi_year) &
                    (repairs['date_dt'].dt.month == kpi_month)
                    ]
            else:
                period_repairs = pd.DataFrame()

            if len(st.session_state.work_days) > 0:
                work_days = st.session_state.work_days.copy()
                work_days['date_dt'] = pd.to_datetime(work_days['date'])
                period_days = work_days[
                    (work_days['date_dt'].dt.year == kpi_year) &
                    (work_days['date_dt'].dt.month == kpi_month)
                    ]
            else:
                period_days = pd.DataFrame()

            kpi_data = []
            for _, emp in st.session_state.employees.iterrows():
                emp_repairs = period_repairs[period_repairs['employees'].str.contains(emp['name'], na=False)] if len(
                    period_repairs) > 0 else pd.DataFrame()
                repairs_count = len(emp_repairs)
                completed_count = len(emp_repairs[emp_repairs['status'] == 'Завершен']) if len(emp_repairs) > 0 else 0

                emp_days = period_days[period_days['employee'] == emp['name']] if len(
                    period_days) > 0 else pd.DataFrame()
                days_worked = len(emp_days)

                fot = days_worked * emp['daily_rate']
                productivity = repairs_count / days_worked if days_worked > 0 else 0
                total_work_days = 22
                load_percent = (days_worked / total_work_days) * 100 if days_worked > 0 else 0

                kpi_data.append({
                    'Сотрудник': emp['name'],
                    'Роль': emp['role'],
                    'Ремонтов': repairs_count,
                    'Завершено': completed_count,
                    'Отработано дней': days_worked,
                    'Загрузка, %': round(load_percent, 1),
                    'Производительность': f"{productivity:.2f} рем/день",
                    'ФОТ, ₽': fot
                })

            kpi_df = pd.DataFrame(kpi_data).sort_values('Ремонтов', ascending=False)
            st.dataframe(kpi_df, use_container_width=True)

            st.markdown("---")
            st.subheader("📊 Визуализация")

            col1, col2 = st.columns(2)
            with col1:
                fig1 = px.bar(kpi_df, x='Сотрудник', y='Ремонтов', title='Количество ремонтов',
                              color='Ремонтов', text='Ремонтов')
                st.plotly_chart(fig1, use_container_width=True)

            with col2:
                fig2 = px.bar(kpi_df, x='Сотрудник', y='Отработано дней', title='Отработанные дни',
                              color='Отработано дней', text='Отработано дней')
                st.plotly_chart(fig2, use_container_width=True)

            col1, col2 = st.columns(2)
            with col1:
                fig3 = px.bar(kpi_df, x='Сотрудник', y='Загрузка, %', title='Загрузка (%)',
                              color='Загрузка, %', text='Загрузка, %')
                st.plotly_chart(fig3, use_container_width=True)

            with col2:
                fig4 = px.bar(kpi_df, x='Сотрудник', y='ФОТ, ₽', title='ФОТ',
                              color='ФОТ, ₽', text='ФОТ, ₽')
                st.plotly_chart(fig4, use_container_width=True)

            if st.button("📥 Экспорт KPI в Excel", use_container_width=True):
                output = BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    kpi_df.to_excel(writer, sheet_name=f'KPI_{kpi_month:02d}_{kpi_year}', index=False)
                st.download_button(
                    label="📥 Скачать Excel",
                    data=output.getvalue(),
                    file_name=f"kpi_{kpi_year}_{kpi_month:02d}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
        else:
            st.info("Нет данных о сотрудниках для расчета KPI")

    def show_settings(self):
        """Настройки с экспортом/импортом данных"""
        st.header("⚙️ Настройки")

        st.subheader("📊 Статистика системы")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Запчастей", len(st.session_state.spare_parts))
        with col2:
            st.metric("Видов работ", len(st.session_state.works))
        with col3:
            st.metric("Сотрудников", len(st.session_state.employees))

        st.markdown("---")

        # ============ НОВЫЙ РАЗДЕЛ: ЭКСПОРТ/ИМПОРТ ДАННЫХ ============
        st.subheader("💾 Ручной экспорт/импорт данных")
        st.info("🔐 Рекомендуется делать резервную копию перед обновлением кода")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### 📤 Экспорт данных")
            st.write("Создает резервную копию всех данных в JSON файл")

            if st.button("📥 Создать резервную копию", use_container_width=True, key="export_backup_btn"):
                # Собираем все данные
                backup_data = {
                    'export_date': datetime.datetime.now().isoformat(),
                    'version': '1.0',
                    'spare_parts': st.session_state.spare_parts.to_dict('records'),
                    'works': st.session_state.works.to_dict('records'),
                    'employees': st.session_state.employees.to_dict('records'),
                    'repairs': st.session_state.repairs.to_dict('records'),
                    'work_days': st.session_state.work_days.to_dict('records'),
                    'statistics': {
                        'total_repairs': len(st.session_state.repairs),
                        'total_employees': len(st.session_state.employees),
                        'total_parts': len(st.session_state.spare_parts),
                        'completed_repairs': len(
                            st.session_state.repairs[st.session_state.repairs['status'] == 'Завершен']) if len(
                            st.session_state.repairs) > 0 else 0
                    }
                }

                # Конвертируем в JSON
                backup_json = json.dumps(backup_data, default=str, ensure_ascii=False, indent=2)

                # Создаем имя файла с датой
                filename = f"erp_backup_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

                st.download_button(
                    label="💾 Скачать резервную копию",
                    data=backup_json,
                    file_name=filename,
                    mime="application/json",
                    use_container_width=True,
                    key="download_backup_btn"
                )
                st.success("✅ Резервная копия создана! Нажмите кнопку выше для скачивания.")

        with col2:
            st.markdown("### 📥 Импорт данных")
            st.write("Восстанавливает данные из ранее созданной резервной копии")

            uploaded_file = st.file_uploader(
                "Выберите файл резервной копии (.json)",
                type=['json'],
                key="restore_uploader"
            )

            if uploaded_file is not None:
                try:
                    # Читаем JSON файл
                    backup_data = json.load(uploaded_file)

                    # Показываем информацию о файле
                    st.info(f"📁 Файл создан: {backup_data.get('export_date', 'Неизвестно')}")
                    st.info(f"📊 Статистика в бэкапе: {backup_data.get('statistics', {})}")

                    col_confirm, col_cancel = st.columns(2)
                    with col_confirm:
                        if st.button("⚠️ Восстановить данные", use_container_width=True, key="confirm_restore_btn"):
                            try:
                                # Восстанавливаем данные
                                if 'spare_parts' in backup_data:
                                    st.session_state.spare_parts = pd.DataFrame(backup_data['spare_parts'])
                                    st.success(f"✅ Восстановлено {len(backup_data['spare_parts'])} запчастей")

                                if 'works' in backup_data:
                                    st.session_state.works = pd.DataFrame(backup_data['works'])
                                    st.success(f"✅ Восстановлено {len(backup_data['works'])} видов работ")

                                if 'employees' in backup_data:
                                    st.session_state.employees = pd.DataFrame(backup_data['employees'])
                                    st.success(f"✅ Восстановлено {len(backup_data['employees'])} сотрудников")

                                if 'repairs' in backup_data:
                                    st.session_state.repairs = pd.DataFrame(backup_data['repairs'])
                                    st.success(f"✅ Восстановлено {len(backup_data['repairs'])} ремонтов")

                                if 'work_days' in backup_data:
                                    st.session_state.work_days = pd.DataFrame(backup_data['work_days'])
                                    st.success(f"✅ Восстановлено {len(backup_data['work_days'])} рабочих дней")

                                # Сохраняем все данные
                                self.save_all()

                                st.success("🎉 Данные успешно восстановлены! Страница будет перезагружена.")
                                st.balloons()
                                time.sleep(2)
                                st.rerun()

                            except Exception as e:
                                st.error(f"❌ Ошибка при восстановлении: {e}")

                    with col_cancel:
                        if st.button("❌ Отмена", use_container_width=True, key="cancel_restore_btn"):
                            st.info("Восстановление отменено")
                            st.rerun()

                except json.JSONDecodeError:
                    st.error("❌ Ошибка: выбранный файл не является корректной резервной копией")
                except Exception as e:
                    st.error(f"❌ Ошибка при чтении файла: {e}")

        st.markdown("---")
        st.subheader("🔄 Автоматическое резервное копирование")
        st.info("💡 Совет: Регулярно создавайте резервные копии перед важными изменениями")

        # Добавляем информацию о последнем бэкапе
        st.caption("📌 Рекомендуется хранить резервные копии в надежном месте (облако, внешний диск)")

        st.markdown("---")

        # ============ ОСТАЛЬНЫЕ НАСТРОЙКИ ============
        st.subheader("📤 Экспорт всех данных в Excel")
        if st.button("📥 Экспорт всех данных в Excel", use_container_width=True):
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                st.session_state.spare_parts.to_excel(writer, sheet_name='Запчасти', index=False)
                st.session_state.works.to_excel(writer, sheet_name='Работы', index=False)
                st.session_state.employees.to_excel(writer, sheet_name='Сотрудники', index=False)
                st.session_state.repairs.to_excel(writer, sheet_name='Ремонты', index=False)
                st.session_state.work_days.to_excel(writer, sheet_name='Рабочие дни', index=False)

            st.download_button(
                label="📥 Скачать Excel файл",
                data=output.getvalue(),
                file_name=f"erp_backup_{datetime.date.today()}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

        st.markdown("---")
        st.subheader("🗑️ Очистка данных")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("🧹 Очистить все ремонты", use_container_width=True):
                # Создаем предупреждение
                st.warning(
                    "⚠️ ВНИМАНИЕ! Это действие необратимо. Рекомендуется сделать резервную копию перед очисткой.")
                confirm = st.checkbox("Я понимаю, что все ремонты будут удалены безвозвратно")
                if confirm:
                    st.session_state.repairs = pd.DataFrame(columns=st.session_state.repairs.columns)
                    self.save_all()
                    st.success("Все ремонты очищены!")
                    st.rerun()

        with col2:
            if st.button("🔄 Сбросить все данные", use_container_width=True):
                st.error("⚠️ ОПАСНО! Это удалит ВСЕ данные без возможности восстановления!")
                confirm = st.checkbox("Я понимаю, что все данные будут безвозвратно удалены")
                confirm2 = st.text_input("Введите 'СБРОСИТЬ' для подтверждения")
                if confirm and confirm2 == "СБРОСИТЬ":
                    for key in ['spare_parts', 'works', 'employees', 'repairs', 'work_days']:
                        if key in st.session_state:
                            del st.session_state[key]
                    self.init_session_state()
                    self.save_all()
                    st.success("Все данные сброшены!")
                    st.rerun()

# ==================== ЗАПУСК ====================
if __name__ == "__main__":
    app = RepairERP()
    app.run()