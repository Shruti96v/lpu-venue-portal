const errorHandler = require('../middlewares/errorHandler');

describe('Error Handler Middleware', () => {
  let mockRequest;
  let mockResponse;
  let nextFunction;

  beforeEach(() => {
    mockRequest = {};
    mockResponse = {
      statusCode: 200,
      status: jest.fn().mockImplementation(function (code) {
        this.statusCode = code;
        return this;
      }),
      json: jest.fn(),
    };
    nextFunction = jest.fn();
    // Silence console.error in tests
    jest.spyOn(console, 'error').mockImplementation(() => {});
  });

  afterEach(() => {
    console.error.mockRestore();
  });

  test('should handle standard error and return 500', () => {
    const error = new Error('Test standard error');

    errorHandler(error, mockRequest, mockResponse, nextFunction);

    expect(mockResponse.status).toHaveBeenCalledWith(500);
    expect(mockResponse.json).toHaveBeenCalledWith({
      success: false,
      message: 'Test standard error',
      stack: expect.any(String),
    });
  });

  test('should handle Mongoose CastError and return 404', () => {
    const error = new Error('Cast Error');
    error.name = 'CastError';
    error.value = 'invalid-id';

    errorHandler(error, mockRequest, mockResponse, nextFunction);

    expect(mockResponse.status).toHaveBeenCalledWith(404);
    expect(mockResponse.json).toHaveBeenCalledWith({
      success: false,
      message: 'Resource not found with id of invalid-id',
      stack: expect.any(String),
    });
  });

  test('should handle Mongoose duplicate key error (code 11000) and return 400', () => {
    const error = new Error('Duplicate key error');
    error.code = 11000;

    errorHandler(error, mockRequest, mockResponse, nextFunction);

    expect(mockResponse.status).toHaveBeenCalledWith(400);
    expect(mockResponse.json).toHaveBeenCalledWith({
      success: false,
      message: 'Duplicate field value entered',
      stack: expect.any(String),
    });
  });

  test('should handle Mongoose ValidationError and return 400', () => {
    const error = new Error('Validation failed');
    error.name = 'ValidationError';
    error.errors = {
      email: { message: 'Email is required' },
      password: { message: 'Password is too short' },
    };

    errorHandler(error, mockRequest, mockResponse, nextFunction);

    expect(mockResponse.status).toHaveBeenCalledWith(400);
    expect(mockResponse.json).toHaveBeenCalledWith({
      success: false,
      message: 'Email is required, Password is too short',
      stack: expect.any(String),
    });
  });
});
