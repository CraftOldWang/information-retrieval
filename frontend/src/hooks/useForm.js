import { useState, useCallback } from 'react';

/**
 * 表单钩子
 * @param {Object} initialValues - 初始表单值
 * @param {Function} validate - 验证函数
 * @param {Function} onSubmit - 提交回调
 * @returns {Object} - 表单状态和方法
 */
const useForm = (initialValues = {}, validate = () => ({}), onSubmit = () => {}) => {
  // 状态
  const [values, setValues] = useState(initialValues);
  const [errors, setErrors] = useState({});
  const [touched, setTouched] = useState({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState(null);
  const [submitSuccess, setSubmitSuccess] = useState(null);
  
  // 重置表单
  const resetForm = useCallback(() => {
    setValues(initialValues);
    setErrors({});
    setTouched({});
    setIsSubmitting(false);
    setSubmitError(null);
    setSubmitSuccess(null);
  }, [initialValues]);
  
  // 设置表单值
  const setFormValues = useCallback((newValues) => {
    setValues(prev => ({ ...prev, ...newValues }));
  }, []);
  
  // 处理输入变化
  const handleChange = useCallback((event) => {
    const { name, value, type, checked } = event.target;
    
    setValues(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
    
    // 如果字段已经被触摸过，重新验证
    if (touched[name]) {
      const validationErrors = validate({ ...values, [name]: type === 'checkbox' ? checked : value });
      setErrors(prev => ({ ...prev, [name]: validationErrors[name] }));
    }
  }, [values, touched, validate]);
  
  // 处理输入失焦
  const handleBlur = useCallback((event) => {
    const { name } = event.target;
    
    setTouched(prev => ({ ...prev, [name]: true }));
    
    // 验证单个字段
    const validationErrors = validate(values);
    setErrors(prev => ({ ...prev, [name]: validationErrors[name] }));
  }, [values, validate]);
  
  // 处理表单提交
  const handleSubmit = useCallback(async (event) => {
    if (event) event.preventDefault();
    
    // 标记所有字段为已触摸
    const allTouched = Object.keys(values).reduce((acc, key) => {
      acc[key] = true;
      return acc;
    }, {});
    setTouched(allTouched);
    
    // 验证所有字段
    const validationErrors = validate(values);
    setErrors(validationErrors);
    
    // 检查是否有错误
    const hasErrors = Object.keys(validationErrors).length > 0;
    
    if (!hasErrors) {
      setIsSubmitting(true);
      setSubmitError(null);
      setSubmitSuccess(null);
      
      try {
        const result = await onSubmit(values);
        setSubmitSuccess(result?.message || '操作成功');
      } catch (error) {
        setSubmitError(error?.message || '操作失败');
      } finally {
        setIsSubmitting(false);
      }
    }
  }, [values, validate, onSubmit]);
  
  // 检查字段是否有错误
  const hasError = useCallback((fieldName) => {
    return touched[fieldName] && errors[fieldName];
  }, [touched, errors]);
  
  // 检查表单是否有效
  const isValid = useCallback(() => {
    const validationErrors = validate(values);
    return Object.keys(validationErrors).length === 0;
  }, [values, validate]);
  
  return {
    // 状态
    values,
    errors,
    touched,
    isSubmitting,
    submitError,
    submitSuccess,
    
    // 方法
    handleChange,
    handleBlur,
    handleSubmit,
    setFormValues,
    resetForm,
    hasError,
    isValid
  };
};

export default useForm;