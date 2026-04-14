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
from collections import Counter

warnings.filterwarnings('ignore')

# ==================== КОНФИГУРАЦИЯ ====================
st.set_page_config(
    page_title="CRM Ремонтный цех Pro",
    page_icon="🔧",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Папка для данных
DATA_FOLDER = Path("erp_data")
DATA_FOLDER.mkdir(exist_ok=True)

# ==================== СОВРЕМЕННЫЙ CSS ДИЗАЙН ====================
st.markdown("""
<style>
    /* Современные переменные */
    :root {
        --primary: #6366f1;
        --primary-dark: #4f46e5;
        --secondary: #10b981;
        --danger: #ef4444;
        --warning: #f59e0b;
        --dark: #1e293b;
        --gray: #64748b;
        --light: #f8fafc;
    }

    /* Главный хедер в стиле CRM */
    .crm-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem 2rem;
        border-radius: 20px;
        color: white;
        margin-bottom: 2rem;
        box-shadow: 0 10px 40px rgba(0,0,0,0.1);
    }

    .crm-header h1 {
        margin: 0;
        font-size: 2rem;
        font-weight: 700;
    }

    .crm-header p {
        margin: 0.5rem 0 0 0;
        opacity: 0.9;
    }

    /* Современные карточки метрик */
    .metric-card-modern {
        background: white;
        border-radius: 20px;
        padding: 1.25rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05), 0 1px 2px rgba(0,0,0,0.1);
        transition: all 0.3s ease;
        border: 1px solid #e2e8f0;
    }

    .metric-card-modern:hover {
        transform: translateY(-4px);
        box-shadow: 0 20px 25px -12px rgba(0,0,0,0.1);
        border-color: #cbd5e1;
    }

    .metric-icon {
        width: 48px;
        height: 48px;
        border-radius: 16px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 24px;
        margin-bottom: 1rem;
    }

    .metric-value {
        font-size: 28px;
        font-weight: 700;
        color: #1e293b;
        margin: 0;
    }

    .metric-label {
        font-size: 14px;
        color: #64748b;
        margin-top: 0.25rem;
    }

    /* Анимации */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }

    .fade-in {
        animation: fadeIn 0.3s ease-out;
    }

    /* Боковая панель - белый текст */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1e293b 0%, #0f172a 100%);
    }

    [data-testid="stSidebar"] .stMarkdown {
        color: white !important;
    }

    [data-testid="stSidebar"] .stMarkdown * {
        color: white !important;
    }

    [data-testid="stSidebar"] .stRadio label {
        color: white !important;
    }

    [data-testid="stSidebar"] .stRadio div {
        color: white !important;
    }

    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] p {
        color: white !important;
    }

    /* Кнопки */
    .stButton > button {
        border-radius: 12px;
        font-weight: 500;
        transition: all 0.2s ease;
        border: none;
    }

    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }

    /* Уведомления */
    .notification-badge {
        background: #ef4444;
        color: white;
        border-radius: 50%;
        padding: 2px 8px;
        font-size: 12px;
        margin-left: 8px;
    }
</style>
""", unsafe_allow_html=True)

# ==================== СПРАВОЧНИК ПРАЗДНИЧНЫХ ДНЕЙ ====================

FIXED_HOLIDAYS = {
    (1, 1): "Новый год",
    (1, 2): "Новый год",
    (1, 3): "Новый год",
    (1, 4): "Новый год",
    (1, 5): "Новый год",
    (1, 6): "Новый год",
    (1, 7): "Рождество Христово",
    (1, 8): "Новогодние каникулы",
    (2, 23): "День защитника Отечества",
    (3, 8): "Международный женский день",
    (5, 1): "Праздник Весны и Труда",
    (5, 9): "День Победы",
    (6, 12): "День России",
    (11, 4): "День народного единства",
}

HOLIDAYS_2026 = {
    datetime.date(2026, 1, 1): "Новый год",
    datetime.date(2026, 1, 2): "Новый год",
    datetime.date(2026, 1, 3): "Новый год",
    datetime.date(2026, 1, 4): "Новый год",
    datetime.date(2026, 1, 5): "Новый год",
    datetime.date(2026, 1, 6): "Новый год",
    datetime.date(2026, 1, 7): "Рождество Христово",
    datetime.date(2026, 1, 8): "Новогодние каникулы",
    datetime.date(2026, 2, 23): "День защитника Отечества",
    datetime.date(2026, 3, 8): "Международный женский день",
    datetime.date(2026, 3, 9): "Перенос с 8 марта",
    datetime.date(2026, 5, 1): "Праздник Весны и Труда",
    datetime.date(2026, 5, 4): "Перенос с 2 мая",
    datetime.date(2026, 5, 9): "День Победы",
    datetime.date(2026, 5, 11): "Перенос с 10 мая",
    datetime.date(2026, 6, 12): "День России",
    datetime.date(2026, 6, 15): "Перенос с 13 июня",
    datetime.date(2026, 11, 4): "День народного единства",
    datetime.date(2026, 11, 3): "Перенос с 1 ноября",
}


def get_holidays_for_year(year):
    if year == 2026:
        return HOLIDAYS_2026.copy()
    holidays = {}
    for (month, day), name in FIXED_HOLIDAYS.items():
        try:
            date = datetime.date(year, month, day)
            holidays[date] = name
        except ValueError:
            pass
    return holidays


def is_holiday(date):
    holidays = get_holidays_for_year(date.year)
    if date in holidays:
        return True, holidays[date]
    return False, ""


def is_weekend(date):
    return date.weekday() >= 5


def get_workday_info(date):
    is_hol, hol_name = is_holiday(date)
    is_week = is_weekend(date)

    if is_hol:
        payment_multiplier = 2.0
        day_type = "holiday"
    else:
        payment_multiplier = 1.0
        day_type = "weekend" if is_week else "workday"

    return {
        'is_holiday': is_hol,
        'holiday_name': hol_name,
        'is_weekend': is_week,
        'payment_multiplier': payment_multiplier,
        'day_type': day_type
    }


def get_advance_dates(year, month):
    advance_dates = []
    try:
        date_5 = datetime.date(year, month, 5)
        advance_dates.append(date_5)
        date_20 = datetime.date(year, month, 20)
        advance_dates.append(date_20)
    except ValueError:
        pass
    return advance_dates


def get_workdays_before_date(employee, target_date, work_days_df):
    if len(work_days_df) == 0:
        return 0, 0, 0

    employee_days = work_days_df[
        (work_days_df['employee'] == employee) &
        (work_days_df['date'] <= target_date.isoformat())
        ]

    total_days = len(employee_days)
    holiday_days = len(
        employee_days[employee_days['is_holiday'] == True]) if 'is_holiday' in employee_days.columns else 0
    regular_days = total_days - holiday_days

    return total_days, regular_days, holiday_days


# ==================== КЛАСС ДЛЯ ЭКСПОРТА ====================
class ExportManager:
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


# ==================== ФУНКЦИИ ДЛЯ MTBF ====================
def calculate_mtbf(repairs_df):
    """
    Расчет MTBF (Mean Time Between Failures)
    Возвращает словарь с показателями MTBF для каждого устройства
    """
    if len(repairs_df) == 0:
        return {
            'mtbf_days': 0,
            'mtbf_hours': 0,
            'total_failures': 0,
            'unique_devices': 0,
            'avg_time_between_failures': 0
        }

    # Копируем данные и сортируем по дате
    df = repairs_df[repairs_df['status'] == 'Завершен'].copy()
    if len(df) == 0:
        return {
            'mtbf_days': 0,
            'mtbf_hours': 0,
            'total_failures': 0,
            'unique_devices': 0,
            'avg_time_between_failures': 0
        }

    df['date_dt'] = pd.to_datetime(df['date_receipt'])
    df = df.sort_values('date_dt')

    # Группируем по устройствам (госномерам)
    device_failures = {}
    for gos_number, group in df.groupby('gos_number'):
        if len(group) > 1:
            # Вычисляем интервалы между отказами для одного устройства
            dates = group['date_dt'].tolist()
            intervals = []
            for i in range(1, len(dates)):
                interval = (dates[i] - dates[i - 1]).total_seconds() / 3600  # в часах
                intervals.append(interval)
            if intervals:
                device_failures[gos_number] = {
                    'failures_count': len(dates),
                    'intervals_hours': intervals,
                    'avg_interval_hours': sum(intervals) / len(intervals)
                }

    # Общий MTBF по всем устройствам
    all_intervals = []
    for device, data in device_failures.items():
        all_intervals.extend(data['intervals_hours'])

    if all_intervals:
        avg_interval_hours = sum(all_intervals) / len(all_intervals)
        return {
            'mtbf_days': round(avg_interval_hours / 24, 1),
            'mtbf_hours': round(avg_interval_hours, 1),
            'total_failures': len(df),
            'unique_devices': len(df['gos_number'].unique()),
            'devices_with_multiple_failures': len(device_failures),
            'avg_time_between_failures': round(avg_interval_hours / 24, 1),
            'device_details': device_failures
        }

    return {
        'mtbf_days': 0,
        'mtbf_hours': 0,
        'total_failures': len(df),
        'unique_devices': len(df['gos_number'].unique()),
        'devices_with_multiple_failures': 0,
        'avg_time_between_failures': 0,
        'device_details': {}
    }


def get_warranty_stats(repairs_df):
    """
    Статистика по гарантийным ремонтам
    """
    if len(repairs_df) == 0:
        return {
            'total_warranty': 0,
            'warranty_percentage': 0,
            'warranty_by_device': {}
        }

    warranty_repairs = repairs_df[repairs_df['repair_type'] == 'Гарантийный ремонт']
    total_warranty = len(warranty_repairs)
    total_repairs = len(repairs_df)

    warranty_percentage = (total_warranty / total_repairs * 100) if total_repairs > 0 else 0

    warranty_by_device = warranty_repairs['gos_number'].value_counts().to_dict()

    return {
        'total_warranty': total_warranty,
        'warranty_percentage': round(warranty_percentage, 1),
        'warranty_by_device': warranty_by_device
    }


# ==================== ОСНОВНОЕ ПРИЛОЖЕНИЕ ====================
class RepairERP:
    def __init__(self):
        self.export_manager = ExportManager()
        self.init_session_state()

    def migrate_work_days(self):
        if len(st.session_state.work_days) > 0:
            if 'is_holiday' not in st.session_state.work_days.columns:
                st.session_state.work_days['is_holiday'] = False
                st.session_state.work_days['holiday_name'] = ''
                st.session_state.work_days['payment_multiplier'] = 1.0

                for idx, row in st.session_state.work_days.iterrows():
                    try:
                        date = datetime.datetime.strptime(row['date'], '%Y-%m-%d').date()
                        work_info = get_workday_info(date)
                        st.session_state.work_days.loc[idx, 'is_holiday'] = work_info['is_holiday']
                        st.session_state.work_days.loc[idx, 'holiday_name'] = work_info['holiday_name']
                        st.session_state.work_days.loc[idx, 'payment_multiplier'] = work_info['payment_multiplier']
                    except:
                        pass

                self.save_all()

    def init_session_state(self):
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

        employees_file = DATA_FOLDER / 'employees.parquet'
        if employees_file.exists():
            st.session_state.employees = pd.read_parquet(employees_file)
        else:
            st.session_state.employees = pd.DataFrame([
                {"name": "Алексей Механик", "role": "Механик", "daily_rate": 5000, "can_elec": False},
                {"name": "Борис Универсал", "role": "Механик-электрик", "daily_rate": 7000, "can_elec": True},
                {"name": "Владимир Универсал", "role": "Механик-электрик", "daily_rate": 7000, "can_elec": True},
                {"name": "Сергей Управляющий", "role": "Управляющий сервисом", "daily_rate": 10000, "can_elec": False},
            ])

        repairs_file = DATA_FOLDER / 'repairs.parquet'
        if repairs_file.exists():
            st.session_state.repairs = pd.read_parquet(repairs_file)
        else:
            st.session_state.repairs = pd.DataFrame(columns=[
                'id', 'gos_number', 'date_receipt', 'date_completion', 'status',
                'repair_type', 'priority', 'employees', 'works', 'parts',
                'parts_cost', 'failure_reason', 'comment', 'tags'
            ])

        workdays_file = DATA_FOLDER / 'work_days.parquet'
        if workdays_file.exists():
            st.session_state.work_days = pd.read_parquet(workdays_file)
        else:
            st.session_state.work_days = pd.DataFrame(columns=[
                'date', 'employee', 'hours_worked', 'repair_ids', 'is_holiday', 'holiday_name', 'payment_multiplier'
            ])

        # История движений
        movement_file = DATA_FOLDER / 'parts_movement.parquet'
        if movement_file.exists():
            st.session_state.parts_movement = pd.read_parquet(movement_file)
        else:
            st.session_state.parts_movement = pd.DataFrame(columns=[
                'date', 'part_name', 'change', 'new_stock', 'type', 'repair_id', 'comment'
            ])

        self.migrate_work_days()

        if 'edit_mode' not in st.session_state:
            st.session_state.edit_mode = {}
        if 'selected_calendar_date' not in st.session_state:
            st.session_state.selected_calendar_date = None
        if 'edit_history_repair' not in st.session_state:
            st.session_state.edit_history_repair = None

    def save_all(self):
        try:
            st.session_state.spare_parts.to_parquet(DATA_FOLDER / 'spare_parts.parquet', index=False)
            st.session_state.works.to_parquet(DATA_FOLDER / 'works.parquet', index=False)
            st.session_state.employees.to_parquet(DATA_FOLDER / 'employees.parquet', index=False)
            st.session_state.repairs.to_parquet(DATA_FOLDER / 'repairs.parquet', index=False)
            st.session_state.work_days.to_parquet(DATA_FOLDER / 'work_days.parquet', index=False)
            st.session_state.parts_movement.to_parquet(DATA_FOLDER / 'parts_movement.parquet', index=False)
            return True
        except Exception as e:
            st.error(f"Ошибка сохранения: {e}")
            return False

    def delete_repair(self, repair_id):
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
                            self.add_movement_record(part_name, qty, 'return', repair_id,
                                                     f"Возврат из удаленного ремонта #{repair_id}")

                st.session_state.repairs = st.session_state.repairs.drop(idx[0]).reset_index(drop=True)
                self.save_all()
                return True
            return False
        except Exception as e:
            st.error(f"Ошибка удаления: {e}")
            return False

    def complete_repair(self, repair_id):
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
        if not parts_list:
            return ""
        return ", ".join([f"{name} x{qty}" for name, qty in parts_list])

    def add_movement_record(self, part_name, change, type, repair_id, comment):
        """Добавление записи в историю движений"""
        current_stock = 0
        part_idx = st.session_state.spare_parts[st.session_state.spare_parts['name'] == part_name].index
        if len(part_idx) > 0:
            current_stock = st.session_state.spare_parts.loc[part_idx[0], 'stock']

        new_record = pd.DataFrame([{
            'date': datetime.datetime.now().isoformat(),
            'part_name': part_name,
            'change': change,
            'new_stock': current_stock,
            'type': type,
            'repair_id': repair_id if repair_id else '',
            'comment': comment
        }])
        st.session_state.parts_movement = pd.concat([st.session_state.parts_movement, new_record], ignore_index=True)

    def check_deficit_alerts(self):
        """Проверка дефицита и создание уведомлений"""
        if len(st.session_state.spare_parts) == 0:
            return []

        low_stock = st.session_state.spare_parts[
            st.session_state.spare_parts['stock'] <= st.session_state.spare_parts['order_point']]
        alerts = []

        for _, part in low_stock.iterrows():
            deficit = part['order_point'] - part['stock']
            if deficit > 0:
                alerts.append({
                    'part_name': part['name'],
                    'current_stock': part['stock'],
                    'order_point': part['order_point'],
                    'deficit': deficit,
                    'severity': 'critical' if part['stock'] == 0 else 'warning'
                })

        return alerts

    def get_employee_load_stats(self):
        """Статистика загрузки сотрудников"""
        if len(st.session_state.employees) == 0 or len(st.session_state.work_days) == 0:
            return []

        stats = []
        for _, emp in st.session_state.employees.iterrows():
            emp_days = st.session_state.work_days[st.session_state.work_days['employee'] == emp['name']]
            days_worked = len(emp_days)

            emp_repairs = st.session_state.repairs[
                st.session_state.repairs['employees'].str.contains(emp['name'], na=False)
            ] if len(st.session_state.repairs) > 0 else pd.DataFrame()
            repairs_count = len(emp_repairs)

            # Загрузка в процентах (22 рабочих дня в месяце)
            load_percent = min(100, (days_worked / 22) * 100)

            status = "🟢 Норма"
            if load_percent < 50 and days_worked > 0:
                status = "🟡 Низкая загрузка"
            elif load_percent > 100:
                status = "🟠 Перегрузка"
            elif days_worked == 0:
                status = "🔴 Не работал"

            stats.append({
                'employee': emp['name'],
                'role': emp['role'],
                'days_worked': days_worked,
                'repairs_count': repairs_count,
                'load_percent': round(load_percent, 1),
                'status': status
            })

        return stats

    def get_seasonal_forecast(self):
        """Прогноз сезонности"""
        if len(st.session_state.repairs) == 0:
            return None

        repairs = st.session_state.repairs.copy()
        repairs['date_dt'] = pd.to_datetime(repairs['date_receipt'])
        repairs['month'] = repairs['date_dt'].dt.month

        # Среднее по месяцам
        monthly_avg = repairs.groupby('month').size().reset_index(name='avg_count')
        monthly_avg['avg_count'] = monthly_avg['avg_count'] / repairs['date_dt'].dt.year.nunique()

        # Прогноз на следующий месяц
        current_month = datetime.date.today().month
        next_month = current_month + 1 if current_month < 12 else 1

        next_month_avg = monthly_avg[monthly_avg['month'] == next_month]['avg_count'].values
        forecast = int(next_month_avg[0]) if len(next_month_avg) > 0 else 0

        return {
            'current_month_avg': int(monthly_avg[monthly_avg['month'] == current_month]['avg_count'].values[0]) if len(
                monthly_avg[monthly_avg['month'] == current_month]) > 0 else 0,
            'next_month_forecast': forecast,
            'monthly_data': monthly_avg
        }

    def add_work_to_repair(self, repair_id, new_work):
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
                    old_stock = st.session_state.spare_parts.loc[part_idx[0], 'stock']
                    st.session_state.spare_parts.loc[part_idx[0], 'stock'] -= quantity
                    self.add_movement_record(part_name, -quantity, 'out', repair_id,
                                             f"Использовано в ремонте #{repair_id}")

                self.save_all()
                return True
            return False
        except Exception as e:
            st.error(f"Ошибка добавления запчасти: {e}")
            return False

    def remove_part_from_repair(self, repair_id, part_name, quantity):
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
                    self.add_movement_record(part_name, quantity, 'in', repair_id, f"Возврат из ремонта #{repair_id}")

                self.save_all()
                return True
            return False
        except Exception as e:
            st.error(f"Ошибка удаления запчасти: {e}")
            return False

    def add_employee(self, name, role, daily_rate):
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
        try:
            st.session_state.employees = st.session_state.employees[
                st.session_state.employees['name'] != employee_name
                ].reset_index(drop=True)
            self.save_all()
            return True
        except Exception as e:
            st.error(f"Ошибка удаления: {e}")
            return False

    def add_repair(self, gos_number, repair_type, employees,
                   failure_reason, works, parts, comment, tags):
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
                'priority': '',
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
                        self.add_movement_record(part_name, -quantity, 'out', new_id,
                                                 f"Использовано в ремонте #{new_id}")

            self.save_all()
            return True
        except Exception as e:
            st.error(f"Ошибка добавления ремонта: {e}")
            return False

    def add_work_day(self, date, employee, hours_worked=8, repair_ids=""):
        try:
            existing = st.session_state.work_days[
                (st.session_state.work_days['date'] == date.isoformat()) &
                (st.session_state.work_days['employee'] == employee)
                ]
            if len(existing) > 0:
                return False, "Сотрудник уже отметился за этот день"

            work_info = get_workday_info(date)
            is_holiday_flag = work_info['is_holiday']
            holiday_name = work_info['holiday_name']
            payment_multiplier = work_info['payment_multiplier']

            new_day = pd.DataFrame([{
                'date': date.isoformat() if isinstance(date, datetime.date) else str(date),
                'employee': employee,
                'hours_worked': hours_worked,
                'repair_ids': repair_ids,
                'is_holiday': is_holiday_flag,
                'holiday_name': holiday_name if is_holiday_flag else '',
                'payment_multiplier': payment_multiplier
            }])
            st.session_state.work_days = pd.concat([st.session_state.work_days, new_day], ignore_index=True)
            self.save_all()

            if is_holiday_flag:
                return True, f"{employee} отметил начало смены {date} (ПРАЗДНИК: {holiday_name} - оплата x2!)"
            else:
                return True, f"{employee} отметил начало смены {date}"
        except Exception as e:
            return False, str(e)

    def delete_work_day(self, work_day_index):
        try:
            st.session_state.work_days = st.session_state.work_days.drop(work_day_index).reset_index(drop=True)
            self.save_all()
            return True
        except Exception as e:
            st.error(f"Ошибка удаления: {e}")
            return False

    def get_parts_forecast(self, target_repairs=200):
        if len(st.session_state.repairs) == 0:
            return pd.DataFrame()

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

        if not parts_usage:
            return pd.DataFrame()

        forecast_data = []
        for part_name, usage in parts_usage.items():
            avg_usage_per_repair = usage['total_used'] / total_repairs_count
            needed_for_target = avg_usage_per_repair * target_repairs

            part_info = st.session_state.spare_parts[
                st.session_state.spare_parts['name'] == part_name
                ]
            current_stock = part_info['stock'].values[0] if len(part_info) > 0 else 0

            recommend = max(0, needed_for_target - current_stock)
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

        forecast_df = pd.DataFrame(forecast_data)
        forecast_df = forecast_df.sort_values('Рекомендуемая закупка', ascending=False)

        return forecast_df

    def get_monthly_forecast(self):
        if len(st.session_state.repairs) == 0:
            return pd.DataFrame()

        repairs = st.session_state.repairs.copy()
        repairs['date_dt'] = pd.to_datetime(repairs['date_receipt'])
        repairs['month'] = repairs['date_dt'].dt.to_period('M')

        monthly_counts = repairs.groupby('month').size()
        avg_monthly_repairs = monthly_counts.mean() if len(monthly_counts) > 0 else 10
        forecast_months = max(1, int(avg_monthly_repairs))

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
            avg_usage_per_repair = usage['total_used'] / total_repairs
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

    def calculate_employee_rating(self, repairs_df, work_days_df):
        """Расчет рейтинга сотрудников"""
        if len(st.session_state.employees) == 0:
            return pd.DataFrame()

        ratings = []
        for _, emp in st.session_state.employees.iterrows():
            emp_repairs = repairs_df[repairs_df['employees'].str.contains(emp['name'], na=False)] if len(
                repairs_df) > 0 else pd.DataFrame()
            emp_days = work_days_df[work_days_df['employee'] == emp['name']] if len(
                work_days_df) > 0 else pd.DataFrame()

            repairs_count = len(emp_repairs)
            days_worked = len(emp_days)
            completed = len(emp_repairs[emp_repairs['status'] == 'Завершен']) if len(emp_repairs) > 0 else 0

            productivity = repairs_count / days_worked if days_worked > 0 else 0
            completion_rate = (completed / repairs_count * 100) if repairs_count > 0 else 0

            productivity_score = min(productivity * 20, 40)
            completion_score = completion_rate * 0.4
            volume_score = min(repairs_count * 2, 20)

            total_rating = productivity_score + completion_score + volume_score

            if total_rating >= 85:
                level = "Эксперт"
                medal = "🥇"
            elif total_rating >= 70:
                level = "Профессионал"
                medal = "🥈"
            elif total_rating >= 50:
                level = "Стажёр"
                medal = "🥉"
            else:
                level = "Новичок"
                medal = "📈"

            ratings.append({
                'Сотрудник': emp['name'],
                'Роль': emp['role'],
                'Ремонтов': repairs_count,
                'Завершено': completed,
                'Производительность': round(productivity, 2),
                'Завершение %': round(completion_rate, 1),
                'Рейтинг': round(total_rating, 1),
                'Уровень': f"{medal} {level}"
            })

        return pd.DataFrame(ratings).sort_values('Рейтинг', ascending=False)

    def show_works_management_simple(self):
        st.markdown('<div class="fade-in">', unsafe_allow_html=True)
        st.header("Управление списком работ")

        tab1, tab2 = st.tabs(["Список работ", "Добавить/Удалить"])

        with tab1:
            st.subheader("Список всех работ")
            search = st.text_input("Поиск", placeholder="Введите название...")
            df = st.session_state.works.copy()
            if search:
                df = df[df['name'].str.contains(search, case=False)]
            st.dataframe(df, use_container_width=True)
            st.info(f"Всего работ: {len(st.session_state.works)}")

        with tab2:
            st.subheader("Добавить новую работу")
            new_work = st.text_input("Название работы", key="new_work_simple")
            if st.button("Добавить", key="add_work_simple", use_container_width=True):
                if new_work and new_work.strip():
                    if new_work in st.session_state.works['name'].values:
                        st.error("Такая работа уже существует!")
                    else:
                        new_row = pd.DataFrame([{'name': new_work}])
                        st.session_state.works = pd.concat([st.session_state.works, new_row], ignore_index=True)
                        self.save_all()
                        st.success(f"Работа '{new_work}' добавлена!")
                        st.rerun()
                else:
                    st.error("Введите название работы!")

            st.markdown("---")
            st.subheader("Удалить работу")
            work_to_delete = st.selectbox("Выберите работу для удаления", st.session_state.works['name'].tolist(),
                                          key="delete_work_simple")
            if st.button("Удалить", key="delete_work_simple_btn", use_container_width=True):
                used = False
                if len(st.session_state.repairs) > 0:
                    for _, repair in st.session_state.repairs.iterrows():
                        if repair['works'] and work_to_delete in repair['works']:
                            used = True
                            break
                if used:
                    st.error(f"Работа '{work_to_delete}' используется в ремонтах и не может быть удалена!")
                else:
                    st.session_state.works = st.session_state.works[
                        st.session_state.works['name'] != work_to_delete].reset_index(drop=True)
                    self.save_all()
                    st.success(f"Работа '{work_to_delete}' удалена!")
                    st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    def show_notifications(self):
        """Отображение уведомлений"""
        st.markdown("---")
        st.markdown("### 🔔 Уведомления")

        # Уведомления о дефиците запчастей
        deficit_alerts = self.check_deficit_alerts()
        if deficit_alerts:
            st.warning(f"⚠️ **Дефицит запчастей:** {len(deficit_alerts)} позиций требуют пополнения!")
            for alert in deficit_alerts[:3]:
                if alert['severity'] == 'critical':
                    st.error(
                        f"🔴 КРИТИЧЕСКИЙ ДЕФИЦИТ: {alert['part_name']} - остаток {alert['current_stock']} шт., требуется {alert['deficit']} шт.!")
                else:
                    st.warning(
                        f"🟡 ВНИМАНИЕ: {alert['part_name']} - остаток {alert['current_stock']} шт., точка заказа {alert['order_point']} шт.")
        else:
            st.success("✅ Все запчасти в достаточном количестве")

        # Уведомления о загрузке сотрудников
        employee_stats = self.get_employee_load_stats()
        if employee_stats:
            low_load = [e for e in employee_stats if e['status'] != '🟢 Норма' and e['days_worked'] > 0]
            not_worked = [e for e in employee_stats if e['days_worked'] == 0]

            if low_load:
                st.info(f"📊 **Загрузка сотрудников:** {len(low_load)} сотрудников с отклонениями")
                for emp in low_load[:3]:
                    st.write(f"  {emp['employee']}: {emp['load_percent']}% загрузки ({emp['status']})")

            if not_worked:
                st.warning(f"👥 **Не работали:** {len(not_worked)} сотрудников не отметили смены")

        # Уведомления о прогнозе
        seasonal_forecast = self.get_seasonal_forecast()
        if seasonal_forecast:
            st.info(
                f"📈 **Прогноз на следующий месяц:** {seasonal_forecast['next_month_forecast']} ремонтов (среднее в текущем: {seasonal_forecast['current_month_avg']})")

    def show_mtbf_analytics(self):
        """Отображение MTBF аналитики"""
        st.markdown("### 📊 MTBF - Mean Time Between Failures")
        st.markdown("Среднее время между отказами (надежность оборудования)")

        mtbf_data = calculate_mtbf(st.session_state.repairs)
        warranty_data = get_warranty_stats(st.session_state.repairs)

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.markdown(f"""
            <div class="metric-card-modern">
                <div class="metric-icon" style="background: #e0e7ff; color: #4f46e5;">⏱️</div>
                <div class="metric-value">{mtbf_data['mtbf_days']} дн.</div>
                <div class="metric-label">MTBF (дней)</div>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            st.markdown(f"""
            <div class="metric-card-modern">
                <div class="metric-icon" style="background: #d1fae5; color: #10b981;">🔄</div>
                <div class="metric-value">{mtbf_data['mtbf_hours']} ч.</div>
                <div class="metric-label">MTBF (часов)</div>
            </div>
            """, unsafe_allow_html=True)

        with col3:
            st.markdown(f"""
            <div class="metric-card-modern">
                <div class="metric-icon" style="background: #fed7aa; color: #f59e0b;">🔧</div>
                <div class="metric-value">{mtbf_data['total_failures']}</div>
                <div class="metric-label">Всего отказов</div>
            </div>
            """, unsafe_allow_html=True)

        with col4:
            st.markdown(f"""
            <div class="metric-card-modern">
                <div class="metric-icon" style="background: #fee2e2; color: #ef4444;">🛡️</div>
                <div class="metric-value">{warranty_data['warranty_percentage']}%</div>
                <div class="metric-label">Гарантийных ремонтов</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("---")

        # Детальная информация по устройствам
        if mtbf_data['devices_with_multiple_failures'] > 0:
            st.subheader("📋 Детализация по устройствам")
            st.info(f"Устройства с повторными обращениями: {mtbf_data['devices_with_multiple_failures']}")

            device_data = []
            for gos_number, data in mtbf_data['device_details'].items():
                device_data.append({
                    'Госномер': gos_number,
                    'Количество отказов': data['failures_count'],
                    'Средний интервал (дни)': round(data['avg_interval_hours'] / 24, 1),
                    'Средний интервал (часы)': round(data['avg_interval_hours'], 1)
                })

            if device_data:
                device_df = pd.DataFrame(device_data).sort_values('Количество отказов', ascending=False)
                st.dataframe(device_df, use_container_width=True)

                fig = px.bar(
                    device_df,
                    x='Госномер',
                    y='Средний интервал (дни)',
                    title='Среднее время между отказами по устройствам (дни)',
                    color='Средний интервал (дни)',
                    text='Средний интервал (дни)'
                )
                fig.update_traces(textposition='outside')
                st.plotly_chart(fig, use_container_width=True)

        else:
            st.info("Нет данных для расчета MTBF (требуется минимум 2 обращения одного устройства)")

        # График надежности
        if len(st.session_state.repairs) > 0:
            st.subheader("📈 Тренд надежности")

            repairs = st.session_state.repairs.copy()
            repairs['date_dt'] = pd.to_datetime(repairs['date_receipt'])
            repairs = repairs.sort_values('date_dt')

            # Группировка по месяцам
            repairs['month'] = repairs['date_dt'].dt.to_period('M')
            monthly_failures = repairs.groupby('month').size().reset_index(name='failures')
            monthly_failures['month_str'] = monthly_failures['month'].astype(str)

            fig = px.line(
                monthly_failures,
                x='month_str',
                y='failures',
                title='Динамика отказов по месяцам',
                markers=True,
                labels={'month_str': 'Месяц', 'failures': 'Количество отказов'}
            )
            fig.update_traces(line=dict(color='#ef4444', width=3))
            st.plotly_chart(fig, use_container_width=True)

    def show_dashboard(self):
        st.markdown('<div class="fade-in">', unsafe_allow_html=True)

        # Показываем уведомления
        self.show_notifications()

        # Показываем MTBF аналитику
        self.show_mtbf_analytics()

        st.markdown("---")

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

        st.markdown("### Ключевые показатели")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.markdown(f"""
            <div class="metric-card-modern">
                <div class="metric-icon" style="background: #e0e7ff; color: #4f46e5;">📦</div>
                <div class="metric-value">{len(st.session_state.spare_parts)}</div>
                <div class="metric-label">Запчастей на складе</div>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            st.markdown(f"""
            <div class="metric-card-modern">
                <div class="metric-icon" style="background: #d1fae5; color: #10b981;">👥</div>
                <div class="metric-value">{len(st.session_state.employees)}</div>
                <div class="metric-label">Сотрудников</div>
            </div>
            """, unsafe_allow_html=True)

        with col3:
            total_repairs = len(period_repairs)
            st.markdown(f"""
            <div class="metric-card-modern">
                <div class="metric-icon" style="background: #fed7aa; color: #f59e0b;">🔧</div>
                <div class="metric-value">{total_repairs}</div>
                <div class="metric-label">Всего ремонтов</div>
            </div>
            """, unsafe_allow_html=True)

        with col4:
            completed = len(period_repairs[period_repairs['status'] == 'Завершен']) if len(period_repairs) > 0 else 0
            st.markdown(f"""
            <div class="metric-card-modern">
                <div class="metric-icon" style="background: #d1fae5; color: #10b981;">✅</div>
                <div class="metric-value">{completed}</div>
                <div class="metric-label">Завершено</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("---")

        if len(period_repairs) > 0:
            col1, col2 = st.columns(2)

            with col1:
                type_counts = period_repairs['repair_type'].value_counts()
                if len(type_counts) > 0:
                    fig = px.pie(
                        values=type_counts.values,
                        names=type_counts.index,
                        title="Распределение по типам ремонта",
                        color_discrete_sequence=px.colors.qualitative.Set3,
                        hole=0.4
                    )
                    fig.update_layout(height=400)
                    st.plotly_chart(fig, use_container_width=True)

            with col2:
                st.info("Выберите период для отображения статистики")
        else:
            st.info("Нет данных для отображения за выбранный период")

        st.markdown("---")
        if len(st.session_state.spare_parts) > 0:
            low_stock = st.session_state.spare_parts[
                st.session_state.spare_parts['stock'] <= st.session_state.spare_parts['order_point']
                ]
            if len(low_stock) > 0:
                st.warning(f"Внимание! {len(low_stock)} запчастей требуют пополнения:")
                st.dataframe(low_stock[['name', 'stock', 'min_stock', 'order_point']], use_container_width=True)
            else:
                st.success("Все запчасти в достаточном количестве")

        st.markdown('</div>', unsafe_allow_html=True)

    def show_repairs(self):
        st.markdown('<div class="fade-in">', unsafe_allow_html=True)
        st.header("Управление ремонтами")

        # Список типов ремонтов
        repair_types = ["Закрытие аренды", "ТО", "Механическое повреждение", "Гарантийный ремонт"]

        # Причины ремонтов
        failure_reasons = ["Износ", "Брак", "Закрытие аренды", "По вине клиента"]

        # Теги
        tags_options = ["Закрытие", "Срочный", "Гарантийный"]

        tab1, tab2, tab3 = st.tabs(["Новый ремонт", "Активные ремонты", "История"])

        with tab1:
            with st.form("new_repair_form", clear_on_submit=True):
                col1, col2 = st.columns(2)

                with col1:
                    gos_number = st.text_input("Госномер *", placeholder="РА201С")
                    repair_type = st.selectbox("Тип ремонта", repair_types)
                    employees = st.multiselect("Исполнители *", st.session_state.employees['name'].tolist())
                    tags = st.multiselect("Теги", tags_options)

                with col2:
                    failure_reason = st.selectbox("Причина", failure_reasons)
                    works_options = st.session_state.works['name'].tolist()
                    works = st.multiselect("Выполняемые работы", works_options)
                    comment = st.text_area("Комментарий", height=100)

                st.subheader("Запчасти")
                parts_options = st.session_state.spare_parts['name'].tolist()
                num_parts = st.number_input("Количество запчастей", 0, 10, 0, key="num_parts_new")

                parts = []
                for i in range(num_parts):
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        part = st.selectbox(f"Запчасть {i + 1}", [""] + parts_options, key=f"new_part_{i}")
                    with col2:
                        qty = st.number_input(f"Кол-во", 1, 100, 1, key=f"new_qty_{i}")
                    if part:
                        parts.append((part, qty))

                st.caption("* - обязательные поля")
                submitted = st.form_submit_button("Принять в ремонт", use_container_width=True)

                if submitted:
                    if not gos_number:
                        st.error("Введите госномер!")
                    elif not employees:
                        st.error("Выберите исполнителей!")
                    else:
                        if self.add_repair(gos_number, repair_type, employees,
                                           failure_reason, works, parts, comment, tags):
                            st.success("Ремонт успешно создан!")
                            st.rerun()
                        else:
                            st.error("Ошибка при создании ремонта!")

        with tab2:
            st.subheader("Активные ремонты")

            if len(st.session_state.repairs) > 0:
                active = st.session_state.repairs[
                    st.session_state.repairs['status'].isin(['В работе', 'Ожидание запчастей'])
                ]

                if len(active) > 0:
                    for idx, repair in active.iterrows():
                        repair_id = repair['id']

                        # Инициализация состояний
                        if f"edit_{repair_id}" not in st.session_state:
                            st.session_state[f"edit_{repair_id}"] = False
                        if f"add_work_{repair_id}" not in st.session_state:
                            st.session_state[f"add_work_{repair_id}"] = False
                        if f"add_part_{repair_id}" not in st.session_state:
                            st.session_state[f"add_part_{repair_id}"] = False

                        with st.expander(f"{repair['gos_number']} - {repair['repair_type']} (ID: {repair['id']})"):

                            if not st.session_state[f"edit_{repair_id}"]:
                                col1, col2, col3 = st.columns(3)
                                with col1:
                                    st.write(f"**Статус:** {repair['status']}")
                                with col2:
                                    st.write(f"**Исполнители:** {repair['employees']}")
                                    st.write(f"**Причина:** {repair['failure_reason']}")
                                with col3:
                                    st.write(f"**Дата приема:** {repair['date_receipt']}")
                                    st.write(f"**Теги:** {repair.get('tags', '—')}")

                                st.markdown("---")
                                st.subheader("Выполняемые работы")
                                if repair['works'] and repair['works'] != '':
                                    works_list = [w.strip() for w in repair['works'].split(',') if w.strip()]
                                    for work_idx, work in enumerate(works_list):
                                        col1, col2 = st.columns([4, 1])
                                        with col1:
                                            st.write(f"- {work}")
                                        with col2:
                                            if st.button(f"🗑️",
                                                         key=f"remove_work_{repair_id}_{work_idx}_{work.replace(' ', '_')}"):
                                                if self.remove_work_from_repair(repair_id, work):
                                                    st.success(f"Работа '{work}' удалена!")
                                                    st.rerun()
                                else:
                                    st.write("Нет добавленных работ")

                                if st.button(f"➕ Добавить работу", key=f"add_work_btn_{repair_id}",
                                             use_container_width=True):
                                    st.session_state[f"add_work_{repair_id}"] = True
                                    st.rerun()

                                st.markdown("---")
                                st.subheader("Используемые запчасти")
                                if repair['parts'] and repair['parts'] != '':
                                    parts_list = self.parse_parts_list(repair['parts'])
                                    for part_idx, (part_name, qty) in enumerate(parts_list):
                                        col1, col2, col3 = st.columns([3, 1, 1])
                                        with col1:
                                            st.write(f"- {part_name}")
                                        with col2:
                                            st.write(f"x{qty}")
                                        with col3:
                                            safe_part_name = part_name.replace(' ', '_').replace('(', '').replace(')',
                                                                                                                  '')
                                            if st.button(f"🗑️",
                                                         key=f"remove_part_{repair_id}_{part_idx}_{safe_part_name}"):
                                                if self.remove_part_from_repair(repair_id, part_name, qty):
                                                    st.success(f"Запчасть '{part_name}' удалена!")
                                                    st.rerun()
                                else:
                                    st.write("Нет добавленных запчастей")

                                if st.button(f"➕ Добавить запчасть", key=f"add_part_btn_{repair_id}",
                                             use_container_width=True):
                                    st.session_state[f"add_part_{repair_id}"] = True
                                    st.rerun()

                                if repair['comment']:
                                    st.markdown("---")
                                    st.info(f"**Комментарий:** {repair['comment']}")

                                st.markdown("---")
                                col1, col2, col3 = st.columns(3)

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
                                st.subheader("Добавление работы")

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
                                st.subheader("Добавление запчасти")

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
                                    try:
                                        repair_type_index = repair_types.index(repair['repair_type'])
                                    except ValueError:
                                        repair_type_index = 0
                                    new_repair_type = st.selectbox("Тип ремонта", repair_types,
                                                                   index=repair_type_index,
                                                                   key=f"edit_type_{repair_id}")

                                with col2:
                                    employees_list = st.session_state.employees['name'].tolist()
                                    current_employees = [e.strip() for e in repair['employees'].split(',')] if repair[
                                        'employees'] else []
                                    new_employees = st.multiselect("Исполнители", employees_list,
                                                                   default=[e for e in current_employees if
                                                                            e in employees_list],
                                                                   key=f"edit_employees_{repair_id}")
                                    try:
                                        reason_index = failure_reasons.index(repair['failure_reason'])
                                    except ValueError:
                                        reason_index = 0
                                    new_failure_reason = st.selectbox("Причина", failure_reasons,
                                                                      index=reason_index,
                                                                      key=f"edit_reason_{repair_id}")

                                current_tags = [t.strip() for t in repair.get('tags', '').split(',')] if repair.get(
                                    'tags') else []
                                new_tags = st.multiselect("Теги", tags_options,
                                                          default=[t for t in current_tags if t in tags_options],
                                                          key=f"edit_tags_{repair_id}")

                                new_comment = st.text_area("Комментарий",
                                                           value=repair['comment'] if repair['comment'] else "",
                                                           key=f"edit_comment_{repair_id}")

                                st.markdown("---")
                                st.subheader("Работы")

                                current_works = [w.strip() for w in repair['works'].split(',')] if repair[
                                    'works'] else []
                                works_options = st.session_state.works['name'].tolist()
                                edited_works = st.multiselect("Список работ", works_options,
                                                              default=[w for w in current_works if w in works_options],
                                                              key=f"edit_works_{repair_id}")

                                st.markdown("---")
                                st.subheader("Запчасти")

                                current_parts = self.parse_parts_list(repair['parts'])
                                st.write("**Текущие запчасти:**")
                                if current_parts:
                                    for part_name, qty in current_parts:
                                        st.write(f"- {part_name} x{qty}")
                                else:
                                    st.write("Нет запчастей")

                                st.write("**Редактирование запчастей:**")
                                parts_options = st.session_state.spare_parts['name'].tolist()
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
            st.subheader("История завершенных ремонтов")

            search_gos = st.text_input("Фильтр по госномеру", placeholder="Введите номер...", key="history_search")

            if len(st.session_state.repairs) > 0:
                completed = st.session_state.repairs[
                    st.session_state.repairs['status'] == 'Завершен'
                    ].copy()

                if search_gos:
                    completed = completed[completed['gos_number'].str.contains(search_gos, case=False, na=False)]

                if len(completed) > 0:
                    for hist_idx, repair in completed.iterrows():
                        repair_id = repair['id']

                        if f"history_edit_{repair_id}" not in st.session_state:
                            st.session_state[f"history_edit_{repair_id}"] = False

                        with st.expander(f"✅ {repair['gos_number']} - завершен {repair['date_completion']}"):

                            if not st.session_state[f"history_edit_{repair_id}"]:
                                col1, col2 = st.columns(2)
                                col1.write(f"**Тип:** {repair['repair_type']}")
                                col1.write(f"**Принят:** {repair['date_receipt']}")
                                col2.write(f"**Завершен:** {repair['date_completion']}")
                                col2.write(f"**Исполнители:** {repair['employees']}")

                                if repair['works']:
                                    st.write(f"**Выполненные работы:** {repair['works']}")
                                if repair['parts']:
                                    st.write(f"**Запчасти:** {repair['parts']}")
                                if repair['comment']:
                                    st.info(f"**Комментарий:** {repair['comment']}")

                                st.markdown("---")
                                col1, col2, col3 = st.columns(3)

                                with col1:
                                    if st.button(f"✏️ Редактировать", key=f"history_edit_btn_{repair_id}",
                                                 use_container_width=True):
                                        st.session_state[f"history_edit_{repair_id}"] = True
                                        st.rerun()

                                with col2:
                                    if st.button(f"🔄 Вернуть в работу", key=f"history_reopen_{repair_id}",
                                                 use_container_width=True):
                                        idx_repair = st.session_state.repairs[
                                            st.session_state.repairs['id'] == repair_id].index
                                        if len(idx_repair) > 0:
                                            st.session_state.repairs.loc[idx_repair[0], 'status'] = 'В работе'
                                            st.session_state.repairs.loc[idx_repair[0], 'date_completion'] = ''
                                            self.save_all()
                                            st.success("Ремонт возвращен в работу!")
                                            st.rerun()

                                with col3:
                                    if st.button(f"🗑️ Удалить", key=f"history_delete_{repair_id}",
                                                 use_container_width=True):
                                        if self.delete_repair(repair_id):
                                            st.success("Ремонт удален из истории!")
                                            st.rerun()

                            else:
                                st.subheader("Редактирование завершенного ремонта")

                                col1, col2 = st.columns(2)
                                with col1:
                                    edit_gos = st.text_input("Госномер", value=repair['gos_number'],
                                                             key=f"history_edit_gos_{repair_id}")
                                    try:
                                        repair_type_index = repair_types.index(repair['repair_type'])
                                    except ValueError:
                                        repair_type_index = 0
                                    edit_repair_type = st.selectbox("Тип ремонта", repair_types,
                                                                    index=repair_type_index,
                                                                    key=f"history_edit_type_{repair_id}")

                                with col2:
                                    employees_list = st.session_state.employees['name'].tolist()
                                    current_employees = [e.strip() for e in repair['employees'].split(',')] if repair[
                                        'employees'] else []
                                    edit_employees = st.multiselect(
                                        "Исполнители",
                                        employees_list,
                                        default=[e for e in current_employees if e in employees_list],
                                        key=f"history_edit_employees_{repair_id}"
                                    )
                                    try:
                                        reason_index = failure_reasons.index(repair['failure_reason'])
                                    except ValueError:
                                        reason_index = 0
                                    edit_failure_reason = st.selectbox("Причина", failure_reasons,
                                                                       index=reason_index,
                                                                       key=f"history_edit_reason_{repair_id}")

                                current_tags = [t.strip() for t in repair.get('tags', '').split(',')] if repair.get(
                                    'tags') else []
                                edit_tags = st.multiselect("Теги", tags_options,
                                                           default=[t for t in current_tags if t in tags_options],
                                                           key=f"history_edit_tags_{repair_id}")

                                edit_comment = st.text_area("Комментарий",
                                                            value=repair['comment'] if repair['comment'] else "",
                                                            key=f"history_edit_comment_{repair_id}")

                                st.markdown("---")
                                st.subheader("Работы")

                                current_works = [w.strip() for w in repair['works'].split(',')] if repair[
                                    'works'] else []
                                works_options = st.session_state.works['name'].tolist()
                                edit_works = st.multiselect("Список работ", works_options,
                                                            default=[w for w in current_works if w in works_options],
                                                            key=f"history_edit_works_{repair_id}")

                                st.markdown("---")
                                st.subheader("Запчасти")

                                current_parts = self.parse_parts_list(repair['parts'])
                                st.write("**Текущие запчасти:**")
                                if current_parts:
                                    for part_name, qty in current_parts:
                                        st.write(f"- {part_name} x{qty}")
                                else:
                                    st.write("Нет запчастей")

                                st.write("**Редактирование запчастей:**")
                                parts_options_hist = st.session_state.spare_parts['name'].tolist()
                                num_edit_parts_hist = st.number_input(
                                    "Количество позиций запчастей",
                                    0, 20,
                                    value=len(current_parts) if current_parts else 1,
                                    key=f"history_num_parts_{repair_id}"
                                )

                                edited_parts_hist = []
                                for i in range(num_edit_parts_hist):
                                    col1, col2, col3 = st.columns([2, 1, 0.5])
                                    default_name = current_parts[i][0] if i < len(current_parts) else (
                                        parts_options_hist[0] if parts_options_hist else "")
                                    default_qty = current_parts[i][1] if i < len(current_parts) else 1

                                    with col1:
                                        default_index = parts_options_hist.index(
                                            default_name) if default_name in parts_options_hist else 0
                                        part_name = st.selectbox(
                                            f"Запчасть {i + 1}",
                                            parts_options_hist,
                                            index=default_index if parts_options_hist else 0,
                                            key=f"history_part_name_{repair_id}_{i}"
                                        )
                                    with col2:
                                        part_qty = st.number_input(
                                            f"Кол-во {i + 1}",
                                            1, 100,
                                            value=default_qty,
                                            key=f"history_part_qty_{repair_id}_{i}"
                                        )
                                    with col3:
                                        keep = st.checkbox("Оставить", value=True,
                                                           key=f"history_keep_part_{repair_id}_{i}")

                                    if keep and part_name:
                                        edited_parts_hist.append((part_name, part_qty))

                                col1, col2 = st.columns(2)
                                with col1:
                                    if st.button("💾 Сохранить изменения", key=f"history_save_{repair_id}",
                                                 use_container_width=True):
                                        updated_data = {
                                            'gos_number': edit_gos,
                                            'repair_type': edit_repair_type,
                                            'employees': ", ".join(edit_employees),
                                            'failure_reason': edit_failure_reason,
                                            'tags': ", ".join(edit_tags),
                                            'comment': edit_comment,
                                            'works': ", ".join(edit_works),
                                            'parts': self.format_parts_string(edited_parts_hist)
                                        }

                                        old_parts_dict = {name: qty for name, qty in current_parts}
                                        new_parts_dict = {name: qty for name, qty in edited_parts_hist}

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
                                            st.session_state[f"history_edit_{repair_id}"] = False
                                            st.rerun()

                                with col2:
                                    if st.button("❌ Отмена", key=f"history_cancel_{repair_id}",
                                                 use_container_width=True):
                                        st.session_state[f"history_edit_{repair_id}"] = False
                                        st.rerun()
                else:
                    st.info("Нет завершенных ремонтов по указанному фильтру")
            else:
                st.info("Нет данных о ремонтах")

        st.markdown('</div>', unsafe_allow_html=True)

    def show_employees(self):
        st.markdown('<div class="fade-in">', unsafe_allow_html=True)
        st.header("Управление сотрудниками")

        tab1, tab2, tab3 = st.tabs(["Список сотрудников", "Добавить", "Редактировать"])

        with tab1:
            if len(st.session_state.employees) > 0:
                display_df = st.session_state.employees.copy()
                display_df['daily_rate'] = display_df['daily_rate'].apply(lambda x: f"{x:,} ₽")
                st.dataframe(display_df, use_container_width=True)

                if st.button("Экспорт списка сотрудников", key="export_employees", use_container_width=True):
                    excel_data = self.export_manager.export_to_excel(
                        st.session_state.employees, "employees.xlsx", "Сотрудники"
                    )
                    st.download_button(
                        label="Скачать Excel",
                        data=excel_data,
                        file_name="employees.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
            else:
                st.info("Нет данных о сотрудниках")

        with tab2:
            st.subheader("Добавление нового сотрудника")
            col1, col2, col3 = st.columns(3)
            with col1:
                new_name = st.text_input("ФИО сотрудника", key="new_name")
            with col2:
                new_role = st.selectbox("Должность", ["Механик", "Механик-электрик", "Управляющий сервисом"],
                                        key="new_role")
            with col3:
                new_rate = st.number_input("Ставка (день)", 0, 15000, 5000, 500, key="new_rate")

            if st.button("Добавить сотрудника", use_container_width=True):
                if new_name:
                    if self.add_employee(new_name, new_role, new_rate):
                        st.success(f"Сотрудник {new_name} добавлен!")
                        st.rerun()
                    else:
                        st.error("Ошибка при добавлении!")
                else:
                    st.error("Введите ФИО сотрудника!")

        with tab3:
            st.subheader("Редактирование сотрудника")
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
                        role_options = ["Механик", "Механик-электрик", "Управляющий сервисом"]
                        edit_role = st.selectbox("Должность",
                                                 role_options,
                                                 index=role_options.index(emp_data['role']) if emp_data[
                                                                                                   'role'] in role_options else 0,
                                                 key="edit_role")
                    with col3:
                        edit_rate = st.number_input("Ставка (день)",
                                                    value=int(emp_data['daily_rate']),
                                                    min_value=0,
                                                    step=500, key="edit_rate")

                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("Сохранить изменения", use_container_width=True):
                            if self.update_employee(selected_employee, edit_name, edit_role, edit_rate):
                                st.success("Данные обновлены!")
                                st.rerun()
                            else:
                                st.error("Ошибка обновления!")

                    with col2:
                        if st.button("Удалить сотрудника", use_container_width=True):
                            if self.delete_employee(selected_employee):
                                st.success(f"Сотрудник {selected_employee} удален!")
                                st.rerun()
                            else:
                                st.error("Ошибка удаления!")
            else:
                st.info("Нет сотрудников для редактирования")

        st.markdown('</div>', unsafe_allow_html=True)

    def show_warehouse(self):
        st.markdown('<div class="fade-in">', unsafe_allow_html=True)
        st.header("Управление складом")

        tab1, tab2, tab3, tab4, tab5 = st.tabs(
            ["Текущие остатки", "Прогноз закупок", "Добавить запчасть", "Пополнение запасов", "История движений"])

        with tab1:
            st.subheader("Текущие остатки")

            search = st.text_input("Поиск запчастей", placeholder="Введите название...")

            df = st.session_state.spare_parts.copy()
            if search:
                df = df[df['name'].str.contains(search, case=False, na=False)]

            df['status'] = df.apply(
                lambda x: "Критический" if x['stock'] <= x['order_point']
                else "Норма" if x['stock'] <= x['min_stock'] * 1.5
                else "Достаточно", axis=1
            )

            st.dataframe(df, use_container_width=True)

            st.markdown("---")
            st.subheader("Быстрое редактирование остатков")

            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                edit_part = st.selectbox("Выберите запчасть", df['name'].tolist(), key="edit_part_select")
            with col2:
                new_stock = st.number_input("Новый остаток", min_value=0, value=0, key="new_stock_value")
            with col3:
                if st.button("Обновить остаток", key="update_stock_btn", use_container_width=True):
                    if edit_part:
                        idx = st.session_state.spare_parts[st.session_state.spare_parts['name'] == edit_part].index[0]
                        old_stock = st.session_state.spare_parts.loc[idx, 'stock']
                        change = new_stock - old_stock
                        st.session_state.spare_parts.loc[idx, 'stock'] = new_stock
                        self.add_movement_record(edit_part, change, 'manual', None,
                                                 f"Ручное изменение: {old_stock} -> {new_stock}")
                        self.save_all()
                        st.success(f"Остаток '{edit_part}' изменен: {old_stock} → {new_stock}")
                        st.rerun()

        with tab2:
            st.subheader("Прогноз закупок запчастей")
            st.info("Прогноз основан на реальной статистике использования запчастей в ремонтах")

            col1, col2 = st.columns(2)
            with col1:
                st.subheader("На 200 ремонтов")
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
                st.subheader("На месяц")
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
            st.subheader("Добавление новой запчасти")
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                new_name = st.text_input("Название", key="new_part_name")
            with col2:
                new_stock = st.number_input("Остаток", 0, 1000, 10, key="new_part_stock")
            with col3:
                new_min = st.number_input("Мин. запас", 0, 100, 5, key="new_part_min")
            with col4:
                new_order = st.number_input("Точка заказа", 0, 100, 8, key="new_part_order")

            if st.button("Добавить запчасть", key="add_part_btn", use_container_width=True):
                if new_name:
                    new_row = pd.DataFrame([{
                        'name': new_name, 'stock': new_stock,
                        'min_stock': new_min, 'order_point': new_order
                    }])
                    st.session_state.spare_parts = pd.concat([st.session_state.spare_parts, new_row], ignore_index=True)
                    self.add_movement_record(new_name, new_stock, 'initial', None, "Начальное добавление")
                    self.save_all()
                    st.success(f"Запчасть '{new_name}' добавлена")
                    st.rerun()

        with tab4:
            st.subheader("Пополнение запасов")
            st.info("Добавьте новые поступления запчастей на склад")

            parts_list = st.session_state.spare_parts['name'].tolist()
            selected_part = st.selectbox("Выберите запчасть для пополнения", parts_list, key="restock_part")

            if selected_part:
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
                    comment = st.text_area("Комментарий к поступлению",
                                           placeholder="Например: новая партия, брак, возврат и т.д.",
                                           key="restock_comment")

                st.markdown("---")

                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Подтвердить поступление", use_container_width=True, key="confirm_restock"):
                        new_stock = current_stock + add_quantity
                        st.session_state.spare_parts.loc[part_idx, 'stock'] = new_stock
                        self.add_movement_record(selected_part, add_quantity, 'in', None, comment)
                        self.save_all()
                        st.success(f"На склад добавлено {add_quantity} шт. '{selected_part}'")
                        st.info(f"Новый остаток: {new_stock} шт. (было: {current_stock})")
                        st.balloons()
                        time.sleep(2)
                        st.rerun()

                with col2:
                    if st.button("Отмена", use_container_width=True, key="cancel_restock"):
                        st.rerun()

        with tab5:
            st.subheader("История движений запчастей")

            if len(st.session_state.parts_movement) > 0:
                movement_df = st.session_state.parts_movement.copy().sort_values('date', ascending=False)

                filter_part = st.selectbox("Фильтр по запчасти",
                                           ["Все"] + st.session_state.spare_parts['name'].tolist())
                if filter_part != "Все":
                    movement_df = movement_df[movement_df['part_name'] == filter_part]

                st.dataframe(movement_df, use_container_width=True)

                col1, col2, col3 = st.columns(3)
                with col1:
                    total_in = movement_df[movement_df['change'] > 0]['change'].sum()
                    st.metric("Всего поступлений", f"{total_in} шт.")
                with col2:
                    total_out = movement_df[movement_df['change'] < 0]['change'].sum()
                    st.metric("Всего расходов", f"{abs(total_out)} шт.")
                with col3:
                    st.metric("Всего операций", len(movement_df))
            else:
                st.info("Нет истории движений")

        st.markdown('</div>', unsafe_allow_html=True)

    def show_analytics(self):
        st.markdown('<div class="fade-in">', unsafe_allow_html=True)
        st.header("Аналитика")

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

        if len(st.session_state.repairs) > 0:
            repairs = st.session_state.repairs.copy()
            repairs['date_dt'] = pd.to_datetime(repairs['date_receipt'])

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
            else:
                period_repairs = repairs[repairs['date_dt'].dt.year == year]
                period_label = str(year)
        else:
            period_repairs = pd.DataFrame()
            period_label = "Нет данных"

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

        tab1, tab2, tab3, tab4, tab5 = st.tabs(
            ["Дашборд", "Ремонты", "KPI сотрудников", "Аналитика склада", "Тепловая карта"])

        with tab1:
            st.subheader(f"Дашборд за {period_label}")

            col1, col2, col3, col4 = st.columns(4)
            with col1:
                total_repairs = len(period_repairs)
                st.metric("Всего ремонтов", total_repairs)
            with col2:
                completed = len(period_repairs[period_repairs['status'] == 'Завершен']) if len(
                    period_repairs) > 0 else 0
                st.metric("Завершено", completed)
            with col3:
                in_progress = len(period_repairs[period_repairs['status'] == 'В работе']) if len(
                    period_repairs) > 0 else 0
                st.metric("В работе", in_progress)
            with col4:
                st.metric("Сотрудников", len(st.session_state.employees))

            st.markdown("---")

            if len(period_repairs) > 0:
                col1, col2 = st.columns(2)
                with col1:
                    type_counts = period_repairs['repair_type'].value_counts()
                    if len(type_counts) > 0:
                        fig = px.pie(
                            values=type_counts.values,
                            names=type_counts.index,
                            title="Распределение по типам ремонта",
                            color_discrete_sequence=px.colors.qualitative.Set3,
                            hole=0.4
                        )
                        fig.update_traces(textposition='inside', textinfo='percent+label')
                        st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Нет данных для отображения")

        with tab2:
            st.subheader(f"Статистика ремонтов за {period_label}")

            if len(period_repairs) > 0:
                col1, col2, col3 = st.columns(3)
                with col1:
                    if analytics_type == "По дням":
                        st.metric("Ремонтов за день", len(period_repairs))
                    elif analytics_type == "По месяцам":
                        days_in_month = calendar.monthrange(year, month)[1]
                        avg_per_day = len(period_repairs) / days_in_month if days_in_month > 0 else 0
                        st.metric("Ремонтов за месяц", len(period_repairs))
                        st.metric("В среднем в день", f"{avg_per_day:.1f}")
                    else:
                        avg_per_month = len(period_repairs) / 12 if len(period_repairs) > 0 else 0
                        st.metric("Ремонтов за год", len(period_repairs))
                        st.metric("В среднем в месяц", f"{avg_per_month:.1f}")

                with col2:
                    in_repair = len(period_repairs[period_repairs['status'] == 'В работе'])
                    closed = len(period_repairs[period_repairs['status'] == 'Завершен'])
                    st.metric("В ремонте", in_repair)
                    st.metric("Закрыто", closed)

                with col3:
                    completion_rate = (closed / len(period_repairs) * 100) if len(period_repairs) > 0 else 0
                    st.metric("Процент завершения", f"{completion_rate:.1f}%")

                st.markdown("---")

                if analytics_type in ["По месяцам", "По годам"]:
                    st.subheader("Динамика поступлений ремонтов")

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
            st.subheader(f"KPI сотрудников за {period_label}")

            if len(st.session_state.employees) > 0:
                total_repairs = len(period_repairs)
                total_employees = len(st.session_state.employees)
                avg_per_employee = total_repairs / total_employees if total_employees > 0 else 0

                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Всего сотрудников", total_employees)
                with col2:
                    st.metric("Всего ремонтов", total_repairs)
                with col3:
                    st.metric("В среднем на сотрудника", f"{avg_per_employee:.1f}")

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
                st.subheader("Визуализация KPI")

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
            st.subheader("Аналитика склада")

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Всего запчастей", len(st.session_state.spare_parts))
            with col2:
                total_stock = st.session_state.spare_parts['stock'].sum() if len(
                    st.session_state.spare_parts) > 0 else 0
                st.metric("Общий остаток", f"{total_stock} шт.")
            with col3:
                deficit_count = len(st.session_state.spare_parts[
                                        st.session_state.spare_parts['stock'] <= st.session_state.spare_parts[
                                            'order_point']
                                        ])
                st.metric("Дефицит", deficit_count)

            st.markdown("---")

            low_stock = st.session_state.spare_parts[
                st.session_state.spare_parts['stock'] <= st.session_state.spare_parts['order_point']
                ]
            if len(low_stock) > 0:
                st.warning(f"Внимание! {len(low_stock)} запчастей требуют пополнения:")
                st.dataframe(low_stock[['name', 'stock', 'min_stock', 'order_point']], use_container_width=True)
            else:
                st.success("Все запчасти в достаточном количестве")

            st.markdown("---")
            st.subheader("Прогноз закупок")

            st.info("Прогноз основан на реальной статистике использования запчастей в ремонтах")

            col1, col2 = st.columns(2)
            with col1:
                st.markdown("### На 200 ремонтов")
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
                st.markdown("### На месяц")
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

        with tab5:
            st.subheader("Тепловая карта загрузки сотрудников")

            if len(st.session_state.employees) > 0 and len(st.session_state.work_days) > 0:
                heatmap_data = []

                heatmap_year = st.selectbox("Год", [2024, 2025, 2026], index=1, key="heatmap_year")
                heatmap_month = st.selectbox("Месяц", range(1, 13), format_func=lambda x: f"{x:02d}",
                                             key="heatmap_month")

                days_in_month = calendar.monthrange(heatmap_year, heatmap_month)[1]
                employees_list = st.session_state.employees['name'].tolist()

                for emp in employees_list:
                    row = {'Сотрудник': emp}
                    for day in range(1, days_in_month + 1):
                        date = datetime.date(heatmap_year, heatmap_month, day)
                        worked = len(st.session_state.work_days[
                                         (st.session_state.work_days['employee'] == emp) &
                                         (st.session_state.work_days['date'] == date.isoformat())
                                         ]) > 0
                        row[f'День {day}'] = 1 if worked else 0
                    heatmap_data.append(row)

                heatmap_df = pd.DataFrame(heatmap_data)
                heatmap_display = heatmap_df.set_index('Сотрудник').T

                fig = px.imshow(
                    heatmap_display,
                    title=f"Тепловая карта загрузки сотрудников за {heatmap_month:02d}.{heatmap_year}",
                    labels=dict(x="Сотрудник", y="День месяца", color="Работал"),
                    color_continuous_scale=[[0, '#fee2e2'], [1, '#22c55e']],
                    aspect="auto"
                )
                fig.update_layout(height=500)
                st.plotly_chart(fig, use_container_width=True)

                total_days = days_in_month * len(employees_list)
                worked_days = sum([sum([v for k, v in row.items() if k != 'Сотрудник']) for row in heatmap_data])
                load_percent = (worked_days / total_days) * 100 if total_days > 0 else 0

                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Всего человеко-дней", f"{worked_days} / {total_days}")
                with col2:
                    st.metric("Общая загрузка", f"{load_percent:.1f}%")
            else:
                st.info("Нет данных о сотрудниках или отработанных днях")

        st.markdown('</div>', unsafe_allow_html=True)

    def show_reports(self):
        st.markdown('<div class="fade-in">', unsafe_allow_html=True)
        st.header("Комплексный отчет")

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
                ["Дашборд", "Ремонты", "KPI сотрудников", "Аналитика склада"])

            with report_tab1:
                st.subheader(f"Сводка за {report_month:02d}.{report_year}")

                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Всего ремонтов", len(period_repairs))
                with col2:
                    completed = len(period_repairs[period_repairs['status'] == 'Завершен'])
                    st.metric("Завершено", completed)
                with col3:
                    st.metric("Сотрудников", len(st.session_state.employees))
                with col4:
                    deficit = len(st.session_state.spare_parts[
                                      st.session_state.spare_parts['stock'] <= st.session_state.spare_parts[
                                          'order_point']
                                      ])
                    st.metric("Дефицит запчастей", deficit)

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

                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Среднее время ремонта", f"{avg_time:.1f} дн.")

            with report_tab2:
                st.subheader("Детальный список ремонтов")

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
                st.subheader("KPI сотрудников")

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

                        fot = 0
                        holiday_days = 0
                        for _, day in emp_days.iterrows():
                            multiplier = day.get('payment_multiplier', 1.0)
                            fot += emp['daily_rate'] * multiplier
                            if day.get('is_holiday', False):
                                holiday_days += 1

                        productivity = repairs_count / days_worked if days_worked > 0 else 0

                        kpi_data.append({
                            'Сотрудник': emp['name'],
                            'Роль': emp['role'],
                            'Ремонтов': repairs_count,
                            'Завершено': completed_count,
                            'Отработано дней': days_worked,
                            'В т.ч. праздничных': holiday_days,
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
                st.subheader("Аналитика склада")

                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Всего запчастей", len(st.session_state.spare_parts))
                    deficit_count = len(st.session_state.spare_parts[
                                            st.session_state.spare_parts['stock'] <= st.session_state.spare_parts[
                                                'order_point']
                                            ])
                    st.metric("Дефицит", deficit_count)

                with col2:
                    total_stock = st.session_state.spare_parts['stock'].sum() if len(
                        st.session_state.spare_parts) > 0 else 0
                    st.metric("Общий остаток", f"{total_stock} шт.")

                st.markdown("---")

                low_stock = st.session_state.spare_parts[
                    st.session_state.spare_parts['stock'] <= st.session_state.spare_parts['order_point']
                    ]
                if len(low_stock) > 0:
                    st.warning("Запчасти, требующие пополнения:")
                    st.dataframe(low_stock[['name', 'stock', 'order_point']], use_container_width=True)
                else:
                    st.success("Все запчасти в достаточном количестве")

                st.markdown("---")
                st.subheader("Прогнозы закупок")

                forecast_200 = self.get_parts_forecast(200)
                if len(forecast_200) > 0:
                    st.caption("Прогноз на 200 ремонтов")
                    st.dataframe(forecast_200.head(10), use_container_width=True)

            st.markdown("---")
            if st.button("Экспорт полного отчета в Excel", use_container_width=True):
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

                            fot = 0
                            holiday_days = 0
                            for _, day in emp_days.iterrows():
                                multiplier = day.get('payment_multiplier', 1.0)
                                fot += emp['daily_rate'] * multiplier
                                if day.get('is_holiday', False):
                                    holiday_days += 1

                            kpi_data.append({
                                'Сотрудник': emp['name'],
                                'Роль': emp['role'],
                                'Ремонтов': len(emp_repairs),
                                'Завершено': len(emp_repairs[emp_repairs['status'] == 'Завершен']),
                                'Отработано дней': len(emp_days),
                                'В т.ч. праздничных': holiday_days,
                                'ФОТ': fot
                            })
                        pd.DataFrame(kpi_data).to_excel(writer, sheet_name='KPI', index=False)

                    st.session_state.spare_parts.to_excel(writer, sheet_name='Склад', index=False)

                    forecast_200 = self.get_parts_forecast(200)
                    if len(forecast_200) > 0:
                        forecast_200.to_excel(writer, sheet_name='Прогноз_200', index=False)

                st.download_button(
                    label="Скачать Excel",
                    data=output.getvalue(),
                    file_name=f"full_report_{report_year}_{report_month:02d}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
        else:
            st.info("Нет данных для формирования отчета")

        st.markdown('</div>', unsafe_allow_html=True)

    def show_work_days(self):
        st.markdown('<div class="fade-in">', unsafe_allow_html=True)
        st.header("Учет отработанных дней")

        with st.expander("Календарь праздничных дней"):
            st.markdown("**Официальные праздничные дни (оплата x2):**")
            col1, col2 = st.columns(2)
            with col1:
                for (month, day), name in sorted(FIXED_HOLIDAYS.items()):
                    if month <= 6:
                        st.write(f"- {day:02d}.{month:02d} - {name}")
            with col2:
                for (month, day), name in sorted(FIXED_HOLIDAYS.items()):
                    if month > 6:
                        st.write(f"- {day:02d}.{month:02d} - {name}")

            st.markdown("---")
            st.markdown("**Оплата:**")
            st.markdown("- Праздничные дни: **x2** (двойная оплата)")
            st.markdown("- Выходные дни (суббота/воскресенье): **x1** (обычная оплата)")
            st.markdown("- Будние дни: **x1** (обычная оплата)")
            st.info("Если праздничный день выпадает на выходной, он всё равно оплачивается x2")

        st.markdown("---")
        st.subheader("Быстрая отметка")

        col1, col2, col3 = st.columns([2, 2, 1])
        with col1:
            selected_employee = st.selectbox("Сотрудник", st.session_state.employees['name'].tolist(),
                                             key="quick_employee")
        with col2:
            work_date = st.date_input("Дата", datetime.date.today(), key="quick_date")
        with col3:
            st.write("")
            st.write("")
            if st.button("Вышел на смену", key="check_in_btn", use_container_width=True):
                work_info = get_workday_info(work_date)
                if work_info['is_holiday']:
                    success, message = self.add_work_day(work_date, selected_employee, 8, "")
                    if success:
                        st.success(f"{message} (ПРАЗДНИЧНЫЙ ДЕНЬ - оплата x2!)")
                        st.balloons()
                        st.rerun()
                    else:
                        st.error(message)
                else:
                    success, message = self.add_work_day(work_date, selected_employee, 8, "")
                    if success:
                        st.success(f"{message}")
                        st.rerun()
                    else:
                        st.error(message)

        st.markdown("---")

        st.subheader("Дни аванса")
        st.info("Аванс выплачивается **5** и **20** числа каждого месяца")

        col1, col2, col3 = st.columns(3)
        with col1:
            advance_month = st.selectbox("Месяц для расчета аванса", range(1, 13),
                                         format_func=lambda x: f"{x:02d}",
                                         index=datetime.date.today().month - 1,
                                         key="advance_month")
        with col2:
            advance_year = st.number_input("Год", value=datetime.date.today().year,
                                           min_value=2024, max_value=2026, key="advance_year")
        with col3:
            if st.button("Рассчитать аванс", use_container_width=True, key="calc_advance"):
                st.rerun()

        advance_dates = get_advance_dates(advance_year, advance_month)

        if len(advance_dates) == 2:
            date_5, date_20 = advance_dates

            tab_5, tab_20 = st.tabs([f"Аванс за 5 число ({date_5.strftime('%d.%m.%Y')})",
                                     f"Аванс за 20 число ({date_20.strftime('%d.%m.%Y')})"])

            with tab_5:
                st.subheader(f"Расчет аванса на {date_5.strftime('%d.%m.%Y')}")

                if len(st.session_state.employees) > 0:
                    advance_data_5 = []

                    for _, emp in st.session_state.employees.iterrows():
                        total_days, regular_days, holiday_days = get_workdays_before_date(
                            emp['name'], date_5, st.session_state.work_days
                        )

                        regular_payment = regular_days * emp['daily_rate']
                        holiday_payment = holiday_days * emp['daily_rate'] * 2
                        total_earned = regular_payment + holiday_payment
                        advance_amount = total_earned * 0.5

                        advance_data_5.append({
                            'Сотрудник': emp['name'],
                            'Должность': emp['role'],
                            'Отработано дней': total_days,
                            'Из них будних/выходных': regular_days,
                            'Из них праздничных (x2)': holiday_days,
                            'Заработано за период': f"{total_earned:,.0f} ₽",
                            'Аванс (50%)': f"{advance_amount:,.0f} ₽"
                        })

                    advance_df_5 = pd.DataFrame(advance_data_5)
                    st.dataframe(advance_df_5, use_container_width=True)

                    total_advance_5 = sum(
                        [float(x['Аванс (50%)'].replace(' ₽', '').replace(',', '')) for x in advance_data_5])
                    st.metric("Общая сумма аванса", f"{total_advance_5:,.0f} ₽")

                    if st.button("Экспорт расчета аванса (5 число)", key="export_advance_5", use_container_width=True):
                        output = BytesIO()
                        with pd.ExcelWriter(output, engine='openpyxl') as writer:
                            advance_df_5.to_excel(writer, sheet_name=f'Аванс_{date_5.strftime("%d.%m")}', index=False)
                        st.download_button(
                            label="Скачать Excel",
                            data=output.getvalue(),
                            file_name=f"advance_{date_5.strftime('%Y%m%d')}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
                else:
                    st.info("Нет данных о сотрудниках")

            with tab_20:
                st.subheader(f"Расчет аванса на {date_20.strftime('%d.%m.%Y')}")

                if len(st.session_state.employees) > 0:
                    advance_data_20 = []

                    for _, emp in st.session_state.employees.iterrows():
                        total_days, regular_days, holiday_days = get_workdays_before_date(
                            emp['name'], date_20, st.session_state.work_days
                        )

                        regular_payment = regular_days * emp['daily_rate']
                        holiday_payment = holiday_days * emp['daily_rate'] * 2
                        total_earned = regular_payment + holiday_payment
                        advance_amount = total_earned * 0.5

                        advance_data_20.append({
                            'Сотрудник': emp['name'],
                            'Должность': emp['role'],
                            'Отработано дней': total_days,
                            'Из них будних/выходных': regular_days,
                            'Из них праздничных (x2)': holiday_days,
                            'Заработано за период': f"{total_earned:,.0f} ₽",
                            'Аванс (50%)': f"{advance_amount:,.0f} ₽"
                        })

                    advance_df_20 = pd.DataFrame(advance_data_20)
                    st.dataframe(advance_df_20, use_container_width=True)

                    total_advance_20 = sum(
                        [float(x['Аванс (50%)'].replace(' ₽', '').replace(',', '')) for x in advance_data_20])
                    st.metric("Общая сумма аванса", f"{total_advance_20:,.0f} ₽")

                    if st.button("Экспорт расчета аванса (20 число)", key="export_advance_20",
                                 use_container_width=True):
                        output = BytesIO()
                        with pd.ExcelWriter(output, engine='openpyxl') as writer:
                            advance_df_20.to_excel(writer, sheet_name=f'Аванс_{date_20.strftime("%d.%m")}', index=False)
                        st.download_button(
                            label="Скачать Excel",
                            data=output.getvalue(),
                            file_name=f"advance_{date_20.strftime('%Y%m%d')}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
                else:
                    st.info("Нет данных о сотрудниках")

        st.markdown("---")

        st.subheader("Календарь рабочих дней")

        col1, col2 = st.columns([3, 1])
        with col1:
            calendar_month = st.selectbox("Месяц", range(1, 13), format_func=lambda x: f"{x:02d}", key="cal_month")
            calendar_year = st.number_input("Год", value=datetime.date.today().year, min_value=2024, max_value=2026,
                                            key="cal_year")
        with col2:
            st.write("")
            st.write("")
            st.markdown("**Легенда:**")
            st.markdown("🟢 **Зеленый** - есть работавшие")
            st.markdown("🔴 **Красный** - нет работавших")
            st.markdown("🟡 **Желтый** - ПРАЗДНИЧНЫЙ день (оплата x2)")
            st.markdown("💰 **Синий** - день аванса (5, 20 число)")

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

        holidays_dict = get_holidays_for_year(calendar_year)
        advance_dates_calendar = get_advance_dates(calendar_year, calendar_month)

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

                    is_holiday_day, holiday_name = is_holiday(current_date)
                    is_advance_day = current_date in advance_dates_calendar

                    if date_str in work_by_date:
                        employees_count = len(work_by_date[date_str])
                        employees_list = ", ".join(work_by_date[date_str])

                        if is_holiday_day:
                            cols[i].markdown(
                                f'<div class="calendar-day" title="ПРАЗДНИК: {holiday_name} | Работали: {employees_list} | Оплата: x2" style="background: #fef3c7; border: 2px solid #f59e0b; border-radius: 12px; padding: 12px; text-align: center;">'
                                f'<b>{day}</b><br>'
                                f'<span style="font-size: 11px;">🎉 {employees_count} чел.</span>'
                                f'<br><span style="background: #f59e0b; color: white; padding: 2px 6px; border-radius: 20px; font-size: 10px;">x2</span>'
                                f'</div>',
                                unsafe_allow_html=True
                            )
                        elif is_advance_day:
                            cols[i].markdown(
                                f'<div class="calendar-day" title="День аванса | Работали: {employees_list}" style="background: #dbeafe; border-color: #3b82f6; border-radius: 12px; padding: 12px; text-align: center;">'
                                f'<b>{day}</b><br>'
                                f'<span style="font-size: 11px;">💰 {employees_count} чел.</span>'
                                f'</div>',
                                unsafe_allow_html=True
                            )
                        else:
                            cols[i].markdown(
                                f'<div class="calendar-day" title="Работали: {employees_list}" style="background: #d1fae5; border-radius: 12px; padding: 12px; text-align: center;">'
                                f'<b>{day}</b><br>'
                                f'<span style="font-size: 11px;">👥 {employees_count}</span>'
                                f'</div>',
                                unsafe_allow_html=True
                            )
                    else:
                        if is_holiday_day:
                            cols[i].markdown(
                                f'<div class="calendar-day" title="ПРАЗДНИК: {holiday_name} (оплата x2)" style="background: #fef3c7; border: 2px solid #f59e0b; border-radius: 12px; padding: 12px; text-align: center;">'
                                f'<b>{day}</b><br>'
                                f'<span style="font-size: 11px;">🎉 {holiday_name[:8]}</span>'
                                f'<br><span style="background: #f59e0b; color: white; padding: 2px 6px; border-radius: 20px; font-size: 10px;">x2</span>'
                                f'</div>',
                                unsafe_allow_html=True
                            )
                        elif is_advance_day:
                            cols[i].markdown(
                                f'<div class="calendar-day" title="День аванса" style="background: #dbeafe; border-color: #3b82f6; border-radius: 12px; padding: 12px; text-align: center;">'
                                f'<b>{day}</b><br>'
                                f'<span style="font-size: 11px;">💰</span>'
                                f'</div>',
                                unsafe_allow_html=True
                            )
                        elif current_date.weekday() >= 5:
                            cols[i].markdown(
                                f'<div class="calendar-day" title="Выходной день (суббота/воскресенье) - оплата x1" style="background: #fee2e2; border-radius: 12px; padding: 12px; text-align: center;">'
                                f'<b>{day}</b><br>'
                                f'<span style="font-size: 11px;">😴</span>'
                                f'</div>',
                                unsafe_allow_html=True
                            )
                        else:
                            cols[i].markdown(
                                f'<div class="calendar-day" title="Рабочий день - оплата x1" style="background: #e2e8f0; border-radius: 12px; padding: 12px; text-align: center;">'
                                f'<b>{day}</b><br>'
                                f'<span style="font-size: 11px;">📅</span>'
                                f'</div>',
                                unsafe_allow_html=True
                            )

        st.markdown("---")

        st.subheader("Детальная информация по дню")

        selected_date = st.date_input("Выберите дату для просмотра", datetime.date.today(), key="detail_date")
        date_str = selected_date.isoformat()

        work_info = get_workday_info(selected_date)
        is_holiday_selected = work_info['is_holiday']
        holiday_name_selected = work_info['holiday_name']
        is_weekend_selected = work_info['is_weekend']
        is_advance_selected = selected_date in get_advance_dates(selected_date.year, selected_date.month)

        col1, col2, col3 = st.columns(3)
        with col1:
            if is_holiday_selected:
                st.info(
                    f"**{selected_date.strftime('%d.%m.%Y')}**\n\n{holiday_name_selected}\n\nОплата: **x2 (праздничный день)**")
            elif is_advance_selected:
                st.info(f"**{selected_date.strftime('%d.%m.%Y')}**\n\nДень аванса\n\nОплата: x1")
            elif is_weekend_selected:
                weekday_name = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"][
                    selected_date.weekday()]
                st.info(f"**{selected_date.strftime('%d.%m.%Y')}**\n\n{weekday_name} (выходной)\n\nОплата: x1")
            else:
                st.info(f"**{selected_date.strftime('%d.%m.%Y')}**\n\nРабочий день\n\nОплата: x1")

        with col2:
            if date_str in work_by_date:
                st.success(f"Работали: {len(work_by_date[date_str])} сотрудников")
            else:
                st.warning("Нет отметок о работе")

        with col3:
            if is_holiday_selected and date_str in work_by_date:
                st.success("Двойная оплата (праздничный день)!")

        if date_str in work_by_date:
            st.markdown("---")
            st.write("**Сотрудники, работавшие в этот день:**")
            for emp in work_by_date[date_str]:
                emp_data = st.session_state.employees[st.session_state.employees['name'] == emp]
                if len(emp_data) > 0:
                    daily_rate = emp_data.iloc[0]['daily_rate']
                    if is_holiday_selected:
                        st.write(
                            f"- {emp} ({emp_data.iloc[0]['role']}) - ставка: {daily_rate:,} ₽ → **{daily_rate * 2:,} ₽** (x2 - праздник)")
                    else:
                        st.write(f"- {emp} ({emp_data.iloc[0]['role']}) - ставка: {daily_rate:,} ₽")

            day_records = st.session_state.work_days[st.session_state.work_days['date'] == date_str]
            if len(day_records) > 0:
                st.write("**Детали:**")
                for _, record in day_records.iterrows():
                    multiplier = record.get('payment_multiplier', 1.0)
                    emp_data = st.session_state.employees[st.session_state.employees['name'] == record['employee']]
                    if len(emp_data) > 0:
                        payment = emp_data.iloc[0]['daily_rate'] * multiplier
                        st.write(
                            f"  - {record['employee']}: {record['hours_worked']} ч., оплата: **{payment:,.0f} ₽** (x{multiplier}), ремонты: {record['repair_ids'] if record['repair_ids'] else '—'}")
        else:
            if is_holiday_selected:
                st.info(f"В {holiday_name_selected} никто не работал")
            else:
                st.info(f"{selected_date.strftime('%d.%m.%Y')} - никто не работал")

        st.markdown("---")

        with st.expander("Полный список отработанных дней"):
            if len(st.session_state.work_days) > 0:
                filtered_days = st.session_state.work_days.copy()
                filtered_days = filtered_days.sort_values('date', ascending=False)

                for idx, day in filtered_days.iterrows():
                    holiday_info = ""
                    if day.get('is_holiday', False):
                        holiday_info = f" ПРАЗДНИК (x{day.get('payment_multiplier', 1.0)})"

                    st.write(f"**{day['date']}** - {day['employee']} - {day['hours_worked']} ч.{holiday_info}")
                    if day.get('holiday_name'):
                        st.write(f"  Праздник: {day['holiday_name']}")
                    if day['repair_ids']:
                        st.write(f"  Ремонты: {day['repair_ids']}")
                    if st.button(f"Удалить", key=f"delete_day_{idx}"):
                        if self.delete_work_day(idx):
                            st.success("Запись удалена!")
                            st.rerun()
                    st.markdown("---")
            else:
                st.info("Нет данных об отработанных днях")

        if len(st.session_state.work_days) > 0:
            st.markdown("---")
            st.subheader("Статистика работы в праздничные дни")

            holiday_work = st.session_state.work_days[st.session_state.work_days['is_holiday'] == True]
            if len(holiday_work) > 0:
                st.info(f"Зафиксировано **{len(holiday_work)}** отработанных дней в праздники (оплата x2)")

                holiday_stats = holiday_work.groupby('employee').size().reset_index(name='праздничных_дней')
                holiday_stats = holiday_stats.merge(st.session_state.employees[['name', 'daily_rate']],
                                                    left_on='employee', right_on='name', how='left')
                holiday_stats['доплата'] = holiday_stats['праздничных_дней'] * holiday_stats['daily_rate']
                holiday_stats = holiday_stats[['employee', 'праздничных_дней', 'доплата']]
                holiday_stats = holiday_stats.sort_values('праздничных_дней', ascending=False)

                st.dataframe(holiday_stats, use_container_width=True)

                fig = px.bar(
                    holiday_stats,
                    x='employee',
                    y='праздничных_дней',
                    title='Количество отработанных праздничных дней по сотрудникам',
                    color='праздничных_дней',
                    text='праздничных_дней'
                )
                fig.update_traces(textposition='outside')
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Нет отработанных дней в праздники")

        st.markdown('</div>', unsafe_allow_html=True)

    def show_employee_kpi(self):
        st.markdown('<div class="fade-in">', unsafe_allow_html=True)
        st.header("KPI сотрудников и рейтинг")

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

            tab_kpi, tab_rating = st.tabs(["KPI показатели", "Рейтинг сотрудников"])

            with tab_kpi:
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

                    fot = 0
                    holiday_days = 0
                    for _, day in emp_days.iterrows():
                        multiplier = day.get('payment_multiplier', 1.0)
                        fot += emp['daily_rate'] * multiplier
                        if day.get('is_holiday', False):
                            holiday_days += 1

                    productivity = repairs_count / days_worked if days_worked > 0 else 0
                    total_work_days = 22
                    load_percent = (days_worked / total_work_days) * 100 if days_worked > 0 else 0

                    kpi_data.append({
                        'Сотрудник': emp['name'],
                        'Роль': emp['role'],
                        'Ремонтов': repairs_count,
                        'Завершено': completed_count,
                        'Отработано дней': days_worked,
                        'В т.ч. праздничных': holiday_days,
                        'Загрузка, %': round(load_percent, 1),
                        'Производительность': f"{productivity:.2f} рем/день",
                        'ФОТ, ₽': fot
                    })

                kpi_df = pd.DataFrame(kpi_data).sort_values('Ремонтов', ascending=False)
                st.dataframe(kpi_df, use_container_width=True)

                st.markdown("---")
                st.subheader("Визуализация")

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

            with tab_rating:
                st.subheader("Рейтинг сотрудников")

                rating_data = []
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
                    completion_rate = (completed_count / repairs_count * 100) if repairs_count > 0 else 0

                    productivity_score = min(productivity * 20, 40)
                    completion_score = completion_rate * 0.4
                    volume_score = min(repairs_count * 2, 20)

                    total_rating = productivity_score + completion_score + volume_score

                    if total_rating >= 85:
                        level = "Эксперт"
                        medal = "🥇"
                    elif total_rating >= 70:
                        level = "Профессионал"
                        medal = "🥈"
                    elif total_rating >= 50:
                        level = "Стажёр"
                        medal = "🥉"
                    else:
                        level = "Новичок"
                        medal = "📈"

                    rating_data.append({
                        'Место': None,
                        'Сотрудник': emp['name'],
                        'Роль': emp['role'],
                        'Ремонтов': repairs_count,
                        'Завершено': completed_count,
                        'Производительность': round(productivity, 2),
                        'Завершение %': round(completion_rate, 1),
                        'Рейтинг': round(total_rating, 1),
                        'Уровень': f"{medal} {level}"
                    })

                rating_df = pd.DataFrame(rating_data).sort_values('Рейтинг', ascending=False).reset_index(drop=True)

                for i in range(len(rating_df)):
                    rating_df.loc[i, 'Место'] = i + 1

                st.dataframe(rating_df, use_container_width=True)

                col1, col2, col3 = st.columns(3)
                if len(rating_df) >= 1:
                    with col1:
                        st.markdown(f"""
                        <div style="text-align: center; background: linear-gradient(135deg, #FFD700, #FFA500); border-radius: 20px; padding: 20px;">
                            <h1 style="margin: 0;">🥇</h1>
                            <h3>{rating_df.iloc[0]['Сотрудник']}</h3>
                            <p>Рейтинг: {rating_df.iloc[0]['Рейтинг']}</p>
                        </div>
                        """, unsafe_allow_html=True)
                if len(rating_df) >= 2:
                    with col2:
                        st.markdown(f"""
                        <div style="text-align: center; background: linear-gradient(135deg, #C0C0C0, #A8A8A8); border-radius: 20px; padding: 20px;">
                            <h1 style="margin: 0;">🥈</h1>
                            <h3>{rating_df.iloc[1]['Сотрудник']}</h3>
                            <p>Рейтинг: {rating_df.iloc[1]['Рейтинг']}</p>
                        </div>
                        """, unsafe_allow_html=True)
                if len(rating_df) >= 3:
                    with col3:
                        st.markdown(f"""
                        <div style="text-align: center; background: linear-gradient(135deg, #CD7F32, #B87333); border-radius: 20px; padding: 20px;">
                            <h1 style="margin: 0;">🥉</h1>
                            <h3>{rating_df.iloc[2]['Сотрудник']}</h3>
                            <p>Рейтинг: {rating_df.iloc[2]['Рейтинг']}</p>
                        </div>
                        """, unsafe_allow_html=True)

                fig = px.bar(
                    rating_df,
                    x='Сотрудник',
                    y='Рейтинг',
                    title='Рейтинг сотрудников',
                    text='Рейтинг',
                    color='Рейтинг',
                    color_continuous_scale='RdYlGn'
                )
                fig.update_traces(textposition='outside')
                st.plotly_chart(fig, use_container_width=True)

            if st.button("Экспорт KPI в Excel", use_container_width=True):
                output = BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    kpi_df.to_excel(writer, sheet_name=f'KPI_{kpi_month:02d}_{kpi_year}', index=False)
                    rating_df.to_excel(writer, sheet_name=f'Рейтинг_{kpi_month:02d}_{kpi_year}', index=False)
                st.download_button(
                    label="Скачать Excel",
                    data=output.getvalue(),
                    file_name=f"kpi_{kpi_year}_{kpi_month:02d}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
        else:
            st.info("Нет данных о сотрудниках для расчета KPI")

        st.markdown('</div>', unsafe_allow_html=True)

    def show_settings(self):
        st.markdown('<div class="fade-in">', unsafe_allow_html=True)
        st.header("Настройки")

        st.subheader("Статистика системы")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Запчастей", len(st.session_state.spare_parts))
        with col2:
            st.metric("Видов работ", len(st.session_state.works))
        with col3:
            st.metric("Сотрудников", len(st.session_state.employees))

        st.markdown("---")

        st.subheader("Ручной экспорт/импорт данных")
        st.info("Рекомендуется делать резервную копию перед обновлением кода")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### Экспорт данных")
            st.write("Создает резервную копию всех данных в JSON файл")

            if st.button("Создать резервную копию", use_container_width=True, key="export_backup_btn"):
                backup_data = {
                    'export_date': datetime.datetime.now().isoformat(),
                    'version': '1.0',
                    'spare_parts': st.session_state.spare_parts.to_dict('records'),
                    'works': st.session_state.works.to_dict('records'),
                    'employees': st.session_state.employees.to_dict('records'),
                    'repairs': st.session_state.repairs.to_dict('records'),
                    'work_days': st.session_state.work_days.to_dict('records'),
                    'parts_movement': st.session_state.parts_movement.to_dict('records'),
                    'statistics': {
                        'total_repairs': len(st.session_state.repairs),
                        'total_employees': len(st.session_state.employees),
                        'total_parts': len(st.session_state.spare_parts),
                        'completed_repairs': len(
                            st.session_state.repairs[st.session_state.repairs['status'] == 'Завершен']) if len(
                            st.session_state.repairs) > 0 else 0
                    }
                }

                backup_json = json.dumps(backup_data, default=str, ensure_ascii=False, indent=2)
                filename = f"erp_backup_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

                st.download_button(
                    label="Скачать резервную копию",
                    data=backup_json,
                    file_name=filename,
                    mime="application/json",
                    use_container_width=True,
                    key="download_backup_btn"
                )
                st.success("Резервная копия создана! Нажмите кнопку выше для скачивания.")

        with col2:
            st.markdown("### Импорт данных")
            st.write("Восстанавливает данные из ранее созданной резервной копии")

            uploaded_file = st.file_uploader(
                "Выберите файл резервной копии (.json)",
                type=['json'],
                key="restore_uploader"
            )

            if uploaded_file is not None:
                try:
                    backup_data = json.load(uploaded_file)
                    st.info(f"Файл создан: {backup_data.get('export_date', 'Неизвестно')}")
                    st.info(f"Статистика в бэкапе: {backup_data.get('statistics', {})}")

                    col_confirm, col_cancel = st.columns(2)
                    with col_confirm:
                        if st.button("Восстановить данные", use_container_width=True, key="confirm_restore_btn"):
                            try:
                                if 'spare_parts' in backup_data:
                                    st.session_state.spare_parts = pd.DataFrame(backup_data['spare_parts'])
                                    st.success(f"Восстановлено {len(backup_data['spare_parts'])} запчастей")
                                if 'works' in backup_data:
                                    st.session_state.works = pd.DataFrame(backup_data['works'])
                                    st.success(f"Восстановлено {len(backup_data['works'])} видов работ")
                                if 'employees' in backup_data:
                                    st.session_state.employees = pd.DataFrame(backup_data['employees'])
                                    st.success(f"Восстановлено {len(backup_data['employees'])} сотрудников")
                                if 'repairs' in backup_data:
                                    st.session_state.repairs = pd.DataFrame(backup_data['repairs'])
                                    st.success(f"Восстановлено {len(backup_data['repairs'])} ремонтов")
                                if 'work_days' in backup_data:
                                    st.session_state.work_days = pd.DataFrame(backup_data['work_days'])
                                    st.success(f"Восстановлено {len(backup_data['work_days'])} рабочих дней")
                                if 'parts_movement' in backup_data:
                                    st.session_state.parts_movement = pd.DataFrame(backup_data['parts_movement'])
                                    st.success(f"Восстановлено {len(backup_data['parts_movement'])} движений")
                                self.save_all()
                                st.success("Данные успешно восстановлены! Страница будет перезагружена.")
                                st.balloons()
                                time.sleep(2)
                                st.rerun()
                            except Exception as e:
                                st.error(f"Ошибка при восстановлении: {e}")
                    with col_cancel:
                        if st.button("Отмена", use_container_width=True, key="cancel_restore_btn"):
                            st.info("Восстановление отменено")
                            st.rerun()
                except json.JSONDecodeError:
                    st.error("Ошибка: выбранный файл не является корректной резервной копией")
                except Exception as e:
                    st.error(f"Ошибка при чтении файла: {e}")

        st.markdown("---")
        st.subheader("Автоматическое резервное копирование")
        st.info("Совет: Регулярно создавайте резервные копии перед важными изменениями")
        st.caption("Рекомендуется хранить резервные копии в надежном месте (облако, внешний диск)")

        st.markdown("---")

        st.subheader("Экспорт всех данных в Excel")
        if st.button("Экспорт всех данных в Excel", use_container_width=True):
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                st.session_state.spare_parts.to_excel(writer, sheet_name='Запчасти', index=False)
                st.session_state.works.to_excel(writer, sheet_name='Работы', index=False)
                st.session_state.employees.to_excel(writer, sheet_name='Сотрудники', index=False)
                st.session_state.repairs.to_excel(writer, sheet_name='Ремонты', index=False)
                st.session_state.work_days.to_excel(writer, sheet_name='Рабочие дни', index=False)
                st.session_state.parts_movement.to_excel(writer, sheet_name='История движений', index=False)

            st.download_button(
                label="Скачать Excel файл",
                data=output.getvalue(),
                file_name=f"erp_backup_{datetime.date.today()}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

        st.markdown("---")
        st.subheader("Очистка данных")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("Очистить все ремонты", use_container_width=True):
                st.warning("ВНИМАНИЕ! Это действие необратимо. Рекомендуется сделать резервную копию перед очисткой.")
                confirm = st.checkbox("Я понимаю, что все ремонты будут удалены безвозвратно")
                if confirm:
                    st.session_state.repairs = pd.DataFrame(columns=st.session_state.repairs.columns)
                    self.save_all()
                    st.success("Все ремонты очищены!")
                    st.rerun()

        with col2:
            if st.button("Сбросить все данные", use_container_width=True):
                st.error("ОПАСНО! Это удалит ВСЕ данные без возможности восстановления!")
                confirm = st.checkbox("Я понимаю, что все данные будут безвозвратно удалены")
                confirm2 = st.text_input("Введите 'СБРОСИТЬ' для подтверждения")
                if confirm and confirm2 == "СБРОСИТЬ":
                    for key in ['spare_parts', 'works', 'employees', 'repairs', 'work_days', 'parts_movement']:
                        if key in st.session_state:
                            del st.session_state[key]
                    self.init_session_state()
                    self.save_all()
                    st.success("Все данные сброшены!")
                    st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)

    def run(self):
        """Запуск приложения"""
        st.markdown("""
        <div class="crm-header">
            <h1>CRM Ремонтный цех PRO</h1>
            <p>Управление ремонтами электровелосипедов</p>
        </div>
        """, unsafe_allow_html=True)

        with st.sidebar:
            st.markdown("### Навигация")

            menu = st.radio(
                "",
                ["Дашборд", "Ремонты", "Сотрудники", "Склад",
                 "Работы", "Аналитика", "Отчеты", "Отработанные дни",
                 "KPI сотрудников", "Настройки"],
                index=0,
                label_visibility="collapsed"
            )

            st.markdown("---")

            if st.button("Сохранить все данные", use_container_width=True):
                if self.save_all():
                    st.success("Данные сохранены!")

        if menu == "Дашборд":
            self.show_dashboard()
        elif menu == "Ремонты":
            self.show_repairs()
        elif menu == "Сотрудники":
            self.show_employees()
        elif menu == "Склад":
            self.show_warehouse()
        elif menu == "Работы":
            self.show_works_management_simple()
        elif menu == "Аналитика":
            self.show_analytics()
        elif menu == "Отчеты":
            self.show_reports()
        elif menu == "Отработанные дни":
            self.show_work_days()
        elif menu == "KPI сотрудников":
            self.show_employee_kpi()
        elif menu == "Настройки":
            self.show_settings()


# ==================== ЗАПУСК ====================
if __name__ == "__main__":
    app = RepairERP()
    app.run()