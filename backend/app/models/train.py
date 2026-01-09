"""火车票查询相关数据模型。"""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import field_validator, Field as PydanticField
from sqlmodel import Field, SQLModel


class Station(SQLModel):
    """车站信息模型（非数据库表，用于API响应）"""
    code: str = PydanticField(description="站点代码")
    name: str = PydanticField(description="站点名称")
    pinyin: str = PydanticField(description="拼音全拼")
    py_code: str = PydanticField(description="拼音首字母")


class StationResponse(SQLModel):
    """车站响应模型"""
    code: str
    name: str
    pinyin: str


class SeatInfo(SQLModel):
    """座位信息"""
    seat_type: str = PydanticField(description="座位类型")
    seat_name: str = PydanticField(description="座位名称")
    available: int = PydanticField(description="余票数量，-1表示无票")
    price: Optional[float] = PydanticField(default=None, description="票价")
    
    @field_validator('available')
    @classmethod
    def validate_available(cls, v: int) -> int:
        """验证余票数量"""
        if v < -1:
            raise ValueError("余票数量不能小于-1")
        return v
    
    @field_validator('price')
    @classmethod
    def validate_price(cls, v: Optional[float]) -> Optional[float]:
        """验证票价"""
        if v is not None and v < 0:
            raise ValueError("票价不能为负数")
        return v


class TrainInfo(SQLModel):
    """车次信息模型"""
    train_no: str = PydanticField(description="车次号")
    train_type: str = PydanticField(description="车次类型：G/D/C/K/T等")
    from_station_code: str = PydanticField(description="出发站代码")
    from_station_name: str = PydanticField(description="出发站名称")
    to_station_code: str = PydanticField(description="到达站代码")
    to_station_name: str = PydanticField(description="到达站名称")
    start_time: str = PydanticField(description="出发时间 HH:MM")
    arrive_time: str = PydanticField(description="到达时间 HH:MM")
    duration: str = PydanticField(description="运行时长 HH:MM")
    seats: List[SeatInfo] = PydanticField(default_factory=list, description="座位信息列表")
    can_buy: bool = PydanticField(default=True, description="是否可购买")
    
    @field_validator('train_no')
    @classmethod
    def validate_train_no(cls, v: str) -> str:
        """验证车次号格式"""
        if not v or len(v) < 2:
            raise ValueError("车次号格式不正确")
        return v
    
    @field_validator('start_time', 'arrive_time', 'duration')
    @classmethod
    def validate_time_format(cls, v: str) -> str:
        """验证时间格式 HH:MM"""
        if not v:
            raise ValueError("时间不能为空")
        parts = v.split(':')
        if len(parts) != 2:
            raise ValueError("时间格式必须为 HH:MM")
        try:
            hours, minutes = int(parts[0]), int(parts[1])
            if hours < 0 or hours > 23 or minutes < 0 or minutes > 59:
                raise ValueError("时间值超出有效范围")
        except ValueError:
            raise ValueError("时间格式不正确")
        return v


class TrainQueryResponse(SQLModel):
    """查询响应模型"""
    trains: List[TrainInfo] = PydanticField(default_factory=list)
    query_time: str = PydanticField(description="查询时间")
    from_cache: bool = PydanticField(default=False, description="是否来自缓存")
    total: int = PydanticField(description="结果总数")
    
    @field_validator('total')
    @classmethod
    def validate_total(cls, v: int) -> int:
        """验证结果总数"""
        if v < 0:
            raise ValueError("结果总数不能为负数")
        return v


class QueryHistory(SQLModel, table=True):
    """查询历史模型（数据库表）"""
    __tablename__ = "query_history"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    from_station_code: str = Field(index=True, min_length=2)
    from_station_name: str
    to_station_code: str = Field(index=True, min_length=2)
    to_station_name: str
    depart_date: str = Field(index=True)
    query_time: datetime = Field(default_factory=datetime.now, index=True)
    user_id: Optional[int] = Field(default=None, foreign_key="user.id", index=True)
