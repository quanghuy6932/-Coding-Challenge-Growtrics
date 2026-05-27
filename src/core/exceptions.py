class DomainException(Exception):
    """Lỗi cha cho tất cả các ngoại lệ thuộc tầng nghiệp vụ (Domain)."""
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class JobNotFoundException(DomainException):
    """Ngoại lệ ném ra khi không tìm thấy Job ID yêu cầu trong hệ thống."""
    def __init__(self, job_id: str):
        super().__init__(f"Video request job with ID '{job_id}' could not be found.")


class InvalidJobStateException(DomainException):
    """Ngoại lệ khi cố tình thay đổi trạng thái Job không đúng quy trình."""
    def __init__(self, message: str):
        super().__init__(message)


class GenerationPipelineException(DomainException):
    """Lỗi xảy ra trong quá trình sinh nội dung video/audio từ phía AI Engine."""
    def __init__(self, message: str, error_code: str = "AI_GENERATION_ERROR"):
        super().__init__(message)
        self.error_code = error_code