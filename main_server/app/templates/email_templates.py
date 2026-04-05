# app/templates/email_templates.py
# 사용자에게 보여줄 임시 html 템플릿

def get_verification_html(verify_url: str = "") -> str:
    """회원가입 인증 메일 HTML 템플릿"""
    return f"""
    <html>
      <body style="font-family: Arial, sans-serif; line-height: 1.6;">
        <div style="max-width: 600px; margin: auto; padding: 20px; border: 1px solid #ddd; border-radius: 10px;">
          <h2 style="color: #2c3e50;">이메일 인증을 완료해주세요</h2>
          <p>잔디 서비스 가입을 환영합니다! 아래 버튼을 클릭하여 인증을 완료해 주세요.</p>
          <div style="text-align: center; margin: 30px 0;">
            <a href="{verify_url}" 
               style="background-color: #4CAF50; color: white; padding: 15px 25px; text-decoration: none; border-radius: 5px; font-weight: bold;">
               이메일 인증하기
            </a>
          </div>
          <p style="color: #7f8c8d; font-size: 0.8em;">본 링크는 1시간 동안만 유효합니다.</p>
        </div>
      </body>
    </html>
    """

def get_verify_success_page_html() -> str:
    """인증 완료 후 브라우저에 보여줄 성공 페이지"""
    return """
    <html>
      <body style="text-align: center; padding: 50px; font-family: Arial;">
        <h2 style="color: #4CAF50;">✅ 인증이 완료되었습니다!</h2>
        <p>이제 잔디 서비스를 정상적으로 이용하실 수 있습니다.</p>
        <p>이 창을 닫고 로그인을 진행해주세요.</p>
      </body>
    </html>
    """

def get_password_reset_html(reset_url: str) -> str:
    """비밀번호 재설정 메일 HTML 템플릿"""
    return f"""
    <html>
      <body style="font-family: Arial, sans-serif; line-height: 1.6;">
        <div style="max-width: 600px; margin: auto; padding: 20px; border: 1px solid #ddd; border-radius: 10px;">
          <h2 style="color: #e74c3c;">비밀번호 재설정 요청</h2>
          <p>계정의 비밀번호를 재설정하려면 아래 버튼을 클릭하세요.</p>
          <div style="text-align: center; margin: 30px 0;">
            <a href="{reset_url}" 
               style="background-color: #3498db; color: white; padding: 15px 25px; text-decoration: none; border-radius: 5px; font-weight: bold;">
               비밀번호 재설정하기
            </a>
          </div>
          <p style="color: #7f8c8d; font-size: 0.8em;">본 링크는 30분 동안만 유효합니다.</p>
        </div>
      </body>
    </html>
    """