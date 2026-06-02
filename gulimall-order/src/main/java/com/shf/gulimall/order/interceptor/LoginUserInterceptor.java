package com.shf.gulimall.order.interceptor;

import com.shf.common.vo.MemberResponseVo;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;
import org.springframework.util.AntPathMatcher;
import org.springframework.web.servlet.HandlerInterceptor;
import org.springframework.web.servlet.ModelAndView;

import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;
import java.io.PrintWriter;

import static com.shf.common.constant.AuthServerConstant.LOGIN_USER;

/**
 * @Description: 登录拦截器
 * @Created: with IntelliJ IDEA.
 * @author: 夏沫止水
 * @createTime: 2020-07-02 18:37
 **/

@Component
public class LoginUserInterceptor implements HandlerInterceptor {

    public static ThreadLocal<MemberResponseVo> loginUser = new ThreadLocal<>();
    private final AntPathMatcher antPathMatcher = new AntPathMatcher();

    @Value("${jrunmall.local-open-seckill-endpoints:false}")
    private boolean localOpenSeckillEndpoints;

    @Override
    public boolean preHandle(HttpServletRequest request, HttpServletResponse response, Object handler) throws Exception {
//        放行所有后台接口
        String orign = request.getHeader("origin");
        if ("http://admin.Jrunmall.com".equalsIgnoreCase(orign)){
            return true;
        }


        String uri = request.getRequestURI();
        boolean match = antPathMatcher.match("/order/order/status/**", uri);
        boolean match1 = antPathMatcher.match("/payed/notify", uri);
        boolean localSeckillApi = antPathMatcher.match("/order/seckill/**", uri)
                || antPathMatcher.match("/order/merchant/seckill-orders", uri)
                || antPathMatcher.match("/order/user/seckill-orders", uri)
                || antPathMatcher.match("/order/internal/seckill-orders/**", uri);
        if (match || match1 || (localOpenSeckillEndpoints && localSeckillApi)) {
            return true;
        }

        //获取登录的用户信息
        MemberResponseVo attribute = (MemberResponseVo) request.getSession().getAttribute(LOGIN_USER);

        if (attribute != null) {
            //把登录后用户的信息放在ThreadLocal里面进行保存
            loginUser.set(attribute);

            return true;
        } else {
            //未登录，返回登录页面
            response.setContentType("text/html;charset=UTF-8");
            PrintWriter out = response.getWriter();
            out.println("<script>alert('请先进行登录，再进行后续操作！');location.href='http://auth.Jrunmall.com/login.html'</script>");
            // session.setAttribute("msg", "请先进行登录");
            // response.sendRedirect("http://auth.Jrunmall.com/login.html");
            return false;
        }
    }

    @Override
    public void postHandle(HttpServletRequest request, HttpServletResponse response, Object handler, ModelAndView modelAndView) throws Exception {

    }

    @Override
    public void afterCompletion(HttpServletRequest request, HttpServletResponse response, Object handler, Exception ex) throws Exception {

    }
}





