"""
对象存储服务 (MinIO)
"""
import uuid
from datetime import timedelta
from typing import Optional, Tuple
from minio import Minio
from minio.error import S3Error

from ..core.config import settings


class OSSService:
    """对象存储服务"""

    def __init__(self):
        self.client = Minio(
            settings.OSS_ENDPOINT.replace("http://", "").replace("https://", ""),
            access_key=settings.OSS_ACCESS_KEY,
            secret_key=settings.OSS_SECRET_KEY,
            secure=False,
        )
        self.bucket = settings.OSS_BUCKET
        self.public_bucket = settings.OSS_PUBLIC_BUCKET

    async def init_buckets(self):
        """初始化存储桶"""
        try:
            if not self.client.bucket_exists(self.bucket):
                self.client.make_bucket(self.bucket)
            if not self.client.bucket_exists(self.public_bucket):
                self.client.make_bucket(self.public_bucket)
        except S3Error as e:
            raise Exception(f"初始化存储桶失败: {str(e)}")

    def generate_object_key(self, filename: str, app_group_id: int) -> str:
        """生成对象存储键"""
        ext = filename.rsplit(".", 1)[-1] if "." in filename else ""
        unique_id = uuid.uuid4().hex
        return f"recordings/{app_group_id}/{unique_id}.{ext}"

    def upload_file(
        self,
        file_data: bytes,
        object_key: str,
        content_type: str = "audio/mpeg",
    ) -> bool:
        """上传文件"""
        try:
            self.client.put_object(
                self.bucket,
                object_key,
                file_data,
                length=len(file_data),
                content_type=content_type,
            )
            return True
        except S3Error as e:
            raise Exception(f"上传文件失败: {str(e)}")

    def upload_part(
        self,
        upload_id: str,
        part_number: int,
        file_data: bytes,
    ) -> dict:
        """分片上传"""
        # 这里简化处理，实际应该使用multipart_upload相关API
        try:
            result = self.client.put_object(
                self.bucket,
                f"temp/{upload_id}/part_{part_number}",
                file_data,
                length=len(file_data),
            )
            return {"etag": result.etag, "part_number": part_number}
        except S3Error as e:
            raise Exception(f"上传分片失败: {str(e)}")

    def complete_multipart_upload(
        self,
        upload_id: str,
        parts: list,
        final_object_key: str,
    ) -> bool:
        """完成分片上传"""
        # 简化处理：实际应该合并分片
        try:
            # 合并所有分片
            # 这里需要读取所有分片并合并
            pass
        except Exception as e:
            raise Exception(f"完成分片上传失败: {str(e)}")

    def get_presigned_url(
        self,
        object_key: str,
        bucket: str = None,
        expires: int = None,
    ) -> str:
        """获取预签名URL（用于安全播放）"""
        try:
            bucket = bucket or self.bucket
            expires = expires or settings.PRESIGNED_URL_EXPIRE
            url = self.client.presigned_get_object(
                bucket,
                object_key,
                expires=timedelta(seconds=expires),
            )
            raise Exception(f"生成预签名URL失败: {str(e)}")

    def get_stream_url(self, object_key: str, bucket: str = None) -> str:
        """获取流式播放URL"""
        return self.get_presigned_url(object_key, bucket, expires=3600)

    def delete_file(self, object_key: str, bucket: str = None) -> bool:
        """删除文件"""
        try:
            bucket = bucket or self.bucket
            self.client.remove_object(bucket, object_key)
            return True
        except S3Error as e:
            raise Exception(f"删除文件失败: {str(e)}")

    def get_file_info(self, object_key: str, bucket: str = None) -> dict:
        """获取文件信息"""
        try:
            bucket = bucket or self.bucket
            stat = self.client.stat_object(bucket, object_key)
            return {
                "size": stat.size,
                "etag": stat.etag,
                "content_type": stat.content_type,
                "last_modified": stat.last_modified,
            }
        except S3Error as e:
            raise Exception(f"获取文件信息失败: {str(e)}")

    def check_file_exists(self, object_key: str, bucket: str = None) -> bool:
        """检查文件是否存在"""
        try:
            bucket = bucket or self.bucket
            self.client.stat_object(bucket, object_key)
            return True
        except S3Error:
            return False

    def copy_file(self, source_key: str, dest_key: str, source_bucket: str = None, dest_bucket: str = None) -> bool:
        """复制文件"""
        try:
            source_bucket = source_bucket or self.bucket
            dest_bucket = dest_bucket or self.bucket
            self.client.copy_object(
                dest_bucket,
                dest_key,
                f"{source_bucket}/{source_key}",
            )
            return True
        except S3Error as e:
            raise Exception(f"复制文件失败: {str(e)}")


oss_service = OSSService()
